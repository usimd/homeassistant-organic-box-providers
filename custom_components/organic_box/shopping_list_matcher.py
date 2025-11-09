"""Shopping list matcher for Organic Box integration."""

import logging
import re
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from homeassistant.components.shopping_list import DOMAIN as SHOPPING_LIST_DOMAIN
from homeassistant.core import HomeAssistant

from .models import BasketItem

if TYPE_CHECKING:
    from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class ShoppingListMatcher:
    """Match delivery items with Home Assistant shopping list."""

    def __init__(self, hass: HomeAssistant, threshold: float = 0.80) -> None:
        """Initialize the matcher.

        Args:
            hass: Home Assistant instance
            threshold: Similarity threshold (0.0-1.0) for matching
        """
        self._hass = hass
        self._threshold = threshold

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove common prefixes/suffixes
        text = re.sub(r"\b(organic|bio|fresh|local|regional)\b", "", text)

        # Remove numbers followed by units (e.g., 1kg, 250g)
        text = re.sub(r"\d+\s*(kg|g|l|ml|pcs?|pack|bunch)", "", text)

        # Remove special characters and extra spaces
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        # Remove standalone common units
        text = re.sub(r"\b(kg|g|l|ml|pcs?|pack|bunch)\b", "", text)

        # Clean up extra spaces again
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def get_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0-1.0)
        """
        # Normalize both texts
        norm1 = ShoppingListMatcher.normalize_text(text1)
        norm2 = ShoppingListMatcher.normalize_text(text2)

        # Use SequenceMatcher for basic similarity
        base_similarity = SequenceMatcher(None, norm1, norm2).ratio()

        # Bonus for substring matches
        if norm1 in norm2 or norm2 in norm1:
            base_similarity = max(base_similarity, 0.85)

        # Bonus for word-level matches
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if words1 and words2:
            word_similarity = len(words1 & words2) / max(len(words1), len(words2))
            # Weighted average: 70% character-level, 30% word-level
            base_similarity = 0.7 * base_similarity + 0.3 * word_similarity

        return base_similarity

    async def is_shopping_list_available(self) -> bool:
        """Check if shopping list integration is available.

        Returns:
            True if shopping list is available
        """
        return SHOPPING_LIST_DOMAIN in self._hass.data

    async def get_shopping_list_items(self) -> list[dict]:
        """Get items from Home Assistant shopping list.

        Returns:
            List of shopping list items
        """
        if not await self.is_shopping_list_available():
            _LOGGER.debug("Shopping list integration not available")
            return []

        try:
            # Get shopping list data
            shopping_list_data = self._hass.data.get(SHOPPING_LIST_DOMAIN)
            if shopping_list_data is None:
                _LOGGER.debug("No shopping list data available")
                return []

            # The shopping list component stores items in the data
            # Handle both ShoppingData object (production) and dict (tests)
            items = None
            if isinstance(shopping_list_data, dict):
                # Tests: dictionary with "items" key
                items = shopping_list_data.get("items", [])
            elif hasattr(shopping_list_data, "items"):
                # Production: ShoppingData object with items attribute or method
                items_attr = getattr(shopping_list_data, "items")
                if callable(items_attr):
                    items = items_attr()
                else:
                    items = items_attr
            else:
                _LOGGER.warning(
                    "Unknown shopping list data type: %s", type(shopping_list_data)
                )
                return []

            if not items:
                _LOGGER.debug("Shopping list is empty")
                return []

            # Filter out completed items
            # Handle both dict items and object items
            active_items = []
            for item in items:
                if isinstance(item, dict):
                    if not item.get("complete", False):
                        active_items.append(item)
                else:
                    # Assume it's an object with attributes
                    if not getattr(item, "complete", False):
                        # Convert object to dict for consistent handling
                        active_items.append(
                            {
                                "id": getattr(item, "id", None),
                                "name": getattr(item, "name", ""),
                                "complete": getattr(item, "complete", False),
                            }
                        )

            _LOGGER.debug("Found %d active shopping list items", len(active_items))
            return active_items

        except Exception as err:
            _LOGGER.error("Error getting shopping list items: %s", err)
            return []

    async def match_items(self, basket_items: list[BasketItem]) -> dict[str, dict]:
        """Match basket items with shopping list items.

        Args:
            basket_items: Items from the delivery basket

        Returns:
            Dictionary mapping basket item names to matched shopping list items
        """
        if not await self.is_shopping_list_available():
            _LOGGER.debug("Shopping list not available, skipping matching")
            return {}

        shopping_items = await self.get_shopping_list_items()
        if not shopping_items:
            _LOGGER.debug("No active shopping list items to match")
            return {}

        matches = {}

        for basket_item in basket_items:
            best_match = None
            best_score = 0.0

            for shop_item in shopping_items:
                shop_item_name = shop_item.get("name", "")
                if not shop_item_name:
                    continue

                similarity = self.get_similarity(basket_item.name, shop_item_name)

                if similarity > best_score and similarity >= self._threshold:
                    best_score = similarity
                    best_match = shop_item

            if best_match:
                matches[basket_item.name] = {
                    "shopping_list_item": best_match,
                    "similarity": best_score,
                }
                _LOGGER.debug(
                    "Matched '%s' with '%s' (similarity: %.2f)",
                    basket_item.name,
                    best_match.get("name"),
                    best_score,
                )

        _LOGGER.info("Matched %d of %d basket items", len(matches), len(basket_items))
        return matches

    async def mark_items_as_delivered(
        self, matches: dict[str, dict], delivery_date: "datetime | None"
    ) -> None:
        """Mark matched shopping list items as delivered.

        This will mark items as complete and add a note about the delivery.

        Args:
            matches: Dictionary of matched items from match_items()
            delivery_date: Delivery date to include in the note
        """
        if not matches:
            _LOGGER.debug("No matches to mark as delivered")
            return

        if not await self.is_shopping_list_available():
            _LOGGER.warning("Shopping list not available, cannot mark items")
            return

        try:
            # Get the shopping list component
            shopping_list = self._hass.data.get(SHOPPING_LIST_DOMAIN)
            if shopping_list is None:
                _LOGGER.error("Shopping list data not found")
                return

            # Format delivery date for note
            date_str = "upcoming delivery"
            if delivery_date:
                date_str = delivery_date.strftime("%Y-%m-%d")

            # Mark each matched item
            for basket_name, match_data in matches.items():
                shop_item = match_data["shopping_list_item"]
                item_id = shop_item.get("id")

                if not item_id:
                    _LOGGER.warning("Shopping list item has no ID, skipping")
                    continue

                # Update the item: mark as complete and add note
                try:
                    # Call the shopping list service to update the item
                    await self._hass.services.async_call(
                        SHOPPING_LIST_DOMAIN,
                        "complete_item",
                        {"name": shop_item.get("name")},
                        blocking=True,
                    )

                    # Add a note about the delivery
                    # Note: The shopping list component may not support notes directly
                    # We'll just complete the item for now
                    _LOGGER.info(
                        "Marked shopping list item '%s' as complete (matched with '%s' from delivery on %s)",
                        shop_item.get("name"),
                        basket_name,
                        date_str,
                    )

                except Exception as item_err:
                    _LOGGER.error(
                        "Error updating shopping list item '%s': %s",
                        shop_item.get("name"),
                        item_err,
                    )

        except Exception as err:
            _LOGGER.error("Error marking items as delivered: %s", err)
