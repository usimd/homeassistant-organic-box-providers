"""Data update coordinator for Organic Box integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ENABLE_SHOPPING_LIST_MATCH,
    CONF_MATCH_THRESHOLD,
    DEFAULT_MATCH_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .models import DeliveryInfo
from .provider import OrganicBoxProvider
from .shopping_list_matcher import ShoppingListMatcher

_LOGGER = logging.getLogger(__name__)


class OrganicBoxDataUpdateCoordinator(DataUpdateCoordinator[DeliveryInfo]):
    """Class to manage fetching Organic Box data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        provider: OrganicBoxProvider,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            provider: The organic box provider instance
            entry: The config entry
        """
        self.provider = provider
        self.entry = entry
        self.matched_items: dict[str, dict] = {}
        self.shopping_list_matcher: ShoppingListMatcher | None = None

        # Call parent init first to set up self.hass
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=entry,
        )

        # Now initialize shopping list matcher (after self.hass is available)
        self._update_shopping_list_matcher()

    def _update_shopping_list_matcher(self) -> None:
        """Update shopping list matcher based on options."""
        if self.entry.options.get(CONF_ENABLE_SHOPPING_LIST_MATCH, False):
            threshold = (
                self.entry.options.get(CONF_MATCH_THRESHOLD, DEFAULT_MATCH_THRESHOLD)
                / 100.0
            )
            self.shopping_list_matcher = ShoppingListMatcher(self.hass, threshold)
            _LOGGER.debug(
                "Shopping list matcher enabled with threshold %.2f", threshold
            )
        else:
            self.shopping_list_matcher = None
            self.matched_items = {}
            _LOGGER.debug("Shopping list matcher disabled")

    async def _async_update_data(self) -> DeliveryInfo:
        """Fetch data from the provider.

        Returns:
            DeliveryInfo object with the latest data

        Raises:
            UpdateFailed: If update fails
        """
        try:
            _LOGGER.debug("Fetching data from %s", self.provider.name)
            delivery_info = await self.provider.get_next_delivery()
            _LOGGER.debug(
                "Successfully fetched data: %d items, delivery date: %s",
                delivery_info.total_items,
                delivery_info.delivery_date,
            )

            # Update shopping list matcher configuration
            self._update_shopping_list_matcher()

            # Match with shopping list if enabled
            if self.shopping_list_matcher and delivery_info.items:
                try:
                    self.matched_items = await self.shopping_list_matcher.match_items(
                        delivery_info.items
                    )

                    # Mark matched items as delivered
                    if self.matched_items:
                        await self.shopping_list_matcher.mark_items_as_delivered(
                            self.matched_items, delivery_info.delivery_date
                        )
                except Exception as match_err:
                    _LOGGER.error("Error matching shopping list items: %s", match_err)
                    # Don't fail the whole update if shopping list matching fails
                    self.matched_items = {}

            return delivery_info
        except Exception as err:
            _LOGGER.error("Error fetching data from provider: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
