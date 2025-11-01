"""OekoBox Online provider implementation."""

import logging
from datetime import datetime

from pyoekoboxonline import OekoboxClient as OekoBoxOnline

from .models import BasketItem, DeliveryInfo
from .provider import OrganicBoxProvider

_LOGGER = logging.getLogger(__name__)


class OekoBoxProvider(OrganicBoxProvider):
    """OekoBox Online provider implementation."""

    def __init__(
        self, username: str, password: str, shop_id: str | None = None
    ) -> None:
        """Initialize the OekoBox provider.

        Args:
            username: The username for authentication
            password: The password for authentication
            shop_id: The shop ID to use for the provider
        """
        super().__init__(username, password)
        self._client: OekoBoxOnline | None = None
        self._shop_id = shop_id

    @property
    def name(self) -> str:
        """Return the name of the provider."""
        return "OekoBox Online"

    async def authenticate(self) -> bool:
        """Authenticate with the OekoBox provider.

        Returns:
            True if authentication was successful, False otherwise
        """
        try:
            self._client = OekoBoxOnline(self._username, self._password)
            if self._shop_id:
                await self._client.logon(self._shop_id)
            else:
                # If no shop_id provided, just initialize without logon
                # This is for the shop selection step
                pass
            self._authenticated = True
            _LOGGER.info("Successfully authenticated with OekoBox Online")
            return True
        except Exception as err:
            _LOGGER.error("Failed to authenticate with OekoBox Online: %s", err)
            self._authenticated = False
            return False

    async def test_connection(self) -> bool:
        """Test the connection to the provider.

        Returns:
            True if connection test was successful, False otherwise
        """
        try:
            if not self._authenticated:
                return await self.authenticate()

            # Try to fetch delivery info as a connection test
            await self.get_next_delivery()
            return True
        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False

    async def get_next_delivery(self) -> DeliveryInfo:
        """Get information about the next delivery.

        Returns:
            DeliveryInfo object containing delivery date and items
        """
        if not self._authenticated or self._client is None:
            if not await self.authenticate():
                raise RuntimeError("Not authenticated with OekoBox Online")

        try:
            # Get next delivery from the API
            delivery_data = await self._client.get_next_delivery()

            # Parse delivery date
            delivery_date = None
            if delivery_data.get("delivery_date"):
                delivery_date = datetime.fromisoformat(delivery_data["delivery_date"])

            # Parse basket items
            items = []
            raw_items = delivery_data.get("items", [])
            for item_data in raw_items:
                item = BasketItem(
                    name=item_data.get("name", "Unknown"),
                    quantity=float(item_data.get("quantity", 0)),
                    unit=item_data.get("unit"),
                    product_id=item_data.get("id"),
                )
                items.append(item)

            return DeliveryInfo(
                delivery_date=delivery_date,
                items=items,
            )
        except Exception as err:
            _LOGGER.error("Failed to get next delivery: %s", err)
            raise

    async def close(self) -> None:
        """Close any open connections."""
        if self._client:
            await self._client.close()
            self._client = None
        self._authenticated = False

    async def get_available_shops(self) -> dict[str, str]:
        """Get available shops for the user.

        Returns:
            Dictionary mapping shop_id to shop name
        """
        if self._client is None:
            self._client = OekoBoxOnline(self._username, self._password)

        try:
            shops_info = await self._client.get_shop_info()
            # Expecting shops_info to be a list of Shop objects or dicts
            # Format: {"shop_id": "Shop Name", ...}
            shops = {}

            if isinstance(shops_info, list):
                for shop in shops_info:
                    # Handle both dict and object attributes
                    if hasattr(shop, "id") and hasattr(shop, "name"):
                        # Shop object
                        shop_id = str(shop.id)
                        shop_name = shop.name
                    elif isinstance(shop, dict):
                        # Dict format
                        shop_id = str(shop.get("id", shop.get("shop_id", "")))
                        shop_name = shop.get(
                            "name", shop.get("shop_name", f"Shop {shop_id}")
                        )
                    else:
                        # Fallback
                        shop_id = str(shop)
                        shop_name = str(shop)

                    if shop_id:
                        shops[shop_id] = shop_name
            elif isinstance(shops_info, dict):
                shops = {str(k): str(v) for k, v in shops_info.items()}

            _LOGGER.debug("Found %d shops for user %s", len(shops), self._username)
            return shops
        except Exception as err:
            _LOGGER.error("Failed to get shop info: %s", err)
            raise
