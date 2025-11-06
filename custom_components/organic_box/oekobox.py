"""OekoBox Online provider implementation."""

import logging
from typing import TYPE_CHECKING

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pyoekoboxonline import OekoboxClient as OekoBoxOnline
from pyoekoboxonline.models import ShopDate, XUnit

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

            # Find the next delivery date from ShopDate objects
            # Filter for ShopDate objects with order_state 0 (pending) or 1 (in preparation/delivery)
            # Exclude order_state 2 (done/past) and -1 (cancelled)
            from datetime import datetime as dt
            from datetime import date as date_type

            now = dt.now().date()

            # Filter for ShopDate objects with order_state 0 (pending) or 1 (in preparation/delivery)
            shop_dates = [d for d in dates if isinstance(d, ShopDate)]

            # Filter for pending/in-progress orders (order_state 0 or 1)
            # and dates that are today or in the future
            # Also exclude dates with order_id == 0 (no delivery planned)
            pending_dates = []
            for shop_date in shop_dates:
                if shop_date.order_state in (0, 1) and shop_date.order_id != 0:
                    # delivery_date should be a datetime.date object
                    if isinstance(shop_date.delivery_date, date_type):
                        date_obj = shop_date.delivery_date
                    elif isinstance(shop_date.delivery_date, dt):
                        date_obj = shop_date.delivery_date.date()
                    else:
                        # Parse if it's a string
                        date_obj = dt.strptime(
                            str(shop_date.delivery_date), "%Y-%m-%d"
                        ).date()

                    if date_obj >= now:
                        pending_dates.append((date_obj, shop_date))

            # Sort by date and get the earliest one
            pending_dates.sort(key=lambda x: x[0])

            delivery_date = None
            next_shop_date = None
            if pending_dates:
                delivery_date, next_shop_date = pending_dates[0]

            # Get orders to find items for the next delivery
            items = []
            if (
                next_shop_date
                and next_shop_date.order_id
                and next_shop_date.order_id > 0
            ):
                # Get items for this specific order
                try:
                    order_items = await self._client.get_order_items(
                        next_shop_date.order_id
                    )

                    # First, separate Items and XUnits, and build a lookup for XUnit overrides
                    item_objects = []
                    xunit_overrides = {}  # item_id -> XUnit

                    for order_item in order_items:
                        if isinstance(order_item, XUnit):
                            # XUnit overrides the unit/quantity for an item
                            if hasattr(order_item, "item_id") and order_item.item_id:
                                xunit_overrides[order_item.item_id] = order_item
                        else:
                            # Regular Item object
                            item_objects.append(order_item)

                    # Process Item objects and apply XUnit overrides if present
                    for order_item in item_objects:
                        item_name = "Unknown"
                        quantity = 0.0
                        unit = None
                        item_id = None

                        # Get item_id and basic info from the Item
                        if hasattr(order_item, "item_id"):
                            item_id = order_item.item_id
                        if hasattr(order_item, "name"):
                            item_name = order_item.name or "Unknown"

                        # Check if there's an XUnit override for this item
                        if item_id and item_id in xunit_overrides:
                            xunit = xunit_overrides[item_id]
                            # XUnit overrides the unit and quantity
                            if hasattr(xunit, "name"):
                                unit = xunit.name  # XUnit.name is the unit name
                            if hasattr(xunit, "parts"):
                                # parts indicates the quantity/amount
                                try:
                                    quantity = float(xunit.parts or 1.0)
                                except (ValueError, TypeError):
                                    quantity = 1.0
                        else:
                            # No XUnit override, use Item's default values
                            if hasattr(order_item, "unit"):
                                unit = order_item.unit
                            if hasattr(order_item, "amount_def"):
                                quantity = float(order_item.amount_def or 1.0)
                            elif hasattr(order_item, "amount"):
                                quantity = float(order_item.amount or 1.0)

                        # Create BasketItem
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
                        next_shop_date.order_id,
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
