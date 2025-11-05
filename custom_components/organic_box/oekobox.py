"""OekoBox Online provider implementation."""

import logging
from typing import TYPE_CHECKING

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pyoekoboxonline import OekoboxClient as OekoBoxOnline

from .models import BasketItem, DeliveryInfo
from .provider import OrganicBoxProvider

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class OekoBoxProvider(OrganicBoxProvider):
    """OekoBox Online provider implementation."""

    def __init__(
        self,
        hass: "HomeAssistant",
        username: str,
        password: str,
        shop_id: str | None = None,
    ) -> None:
        """Initialize the OekoBox provider.

        Args:
            hass: Home Assistant instance
            username: The username for authentication
            password: The password for authentication
            shop_id: The shop ID to use for the provider
        """
        super().__init__(hass, username, password)
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
            if not self._shop_id:
                _LOGGER.error("Cannot authenticate without shop_id")
                self._authenticated = False
                return False

            # Get the aiohttp client session from Home Assistant
            session = async_get_clientsession(self._hass)

            # Initialize client with shop_id, username, password, and session
            self._client = OekoBoxOnline(
                shop_id=self._shop_id,
                username=self._username,
                password=self._password,
                session=session,
            )

            # Perform login (guest=False for user authentication)
            await self._client.logon(guest=False)

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
            # Get delivery dates from the API
            dates = await self._client.get_dates()

            # Find the next delivery date (DDate objects)
            delivery_date = None
            next_ddate = None

            # Filter for DDate objects and find the next upcoming one
            from datetime import datetime as dt
            from pyoekoboxonline import DDate

            now = dt.now().date()
            ddates = [d for d in dates if isinstance(d, DDate)]

            for ddate in ddates:
                if ddate.delivery_date:
                    # Parse delivery_date string (format: YYYY-MM-DD)
                    date_str = ddate.delivery_date
                    date_obj = dt.strptime(date_str, "%Y-%m-%d").date()

                    if date_obj >= now:
                        if delivery_date is None or date_obj < delivery_date:
                            delivery_date = date_obj
                            next_ddate = ddate

            # Get orders to find items for the next delivery
            items = []
            if next_ddate and next_ddate.delivery_date:
                orders = await self._client.get_orders()

                # Find orders matching the delivery date
                from pyoekoboxonline import Order

                for order in orders:
                    if (
                        isinstance(order, Order)
                        and order.ddate == next_ddate.delivery_date
                    ):
                        # Get items for this order
                        try:
                            order_items = await self._client.get_order_items(order.id)

                            # Convert order items to BasketItem objects
                            for order_item in order_items:
                                # order_item is likely an OrderItem or CartItem
                                item_name = "Unknown"
                                quantity = 0.0
                                unit = None
                                item_id = None

                                # Try to get attributes (handles both dict and object)
                                if hasattr(order_item, "item_id"):
                                    item_id = order_item.item_id
                                if hasattr(order_item, "amount"):
                                    quantity = float(order_item.amount or 0)
                                if hasattr(order_item, "unit"):
                                    unit = order_item.unit

                                # Try to get the item details for the name
                                if item_id:
                                    item_details = await self._client.get_item(item_id)
                                    if hasattr(item_details, "name"):
                                        item_name = item_details.name
                                    elif isinstance(item_details, dict):
                                        item_name = item_details.get("name", "Unknown")

                                item = BasketItem(
                                    name=item_name,
                                    quantity=quantity,
                                    unit=unit,
                                    product_id=str(item_id) if item_id else None,
                                )
                                items.append(item)
                        except Exception as item_err:
                            _LOGGER.warning(
                                "Failed to get order items for order %s: %s",
                                order.id,
                                item_err,
                            )

            # Convert date to datetime if found
            delivery_datetime = None
            if delivery_date:
                delivery_datetime = dt.combine(delivery_date, dt.min.time())

            return DeliveryInfo(
                delivery_date=delivery_datetime,
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
