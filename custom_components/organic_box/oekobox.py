"""OekoBox Online provider implementation."""

import logging
from datetime import date as date_type
from datetime import datetime as dt
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pyoekoboxonline import OekoboxClient as OekoBoxOnline
from pyoekoboxonline.exceptions import OekoboxAPIError
from pyoekoboxonline.models import Pause, ShopDate, XUnit

from .const import CONF_AUTO_CANCEL_ON_PAUSE_CONFLICT
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
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the OekoBox provider.

        Args:
            hass: Home Assistant instance
            username: The username for authentication
            password: The password for authentication
            shop_id: The shop ID to use for the provider
            config_entry: The config entry for accessing options
        """
        super().__init__(hass, username, password)
        self._client: OekoBoxOnline | None = None
        self._shop_id = shop_id
        self._config_entry = config_entry
        self._auto_cancel_on_pause_conflict = False

        # Load auto_cancel option from config_entry
        if config_entry:
            self._auto_cancel_on_pause_conflict = config_entry.options.get(
                CONF_AUTO_CANCEL_ON_PAUSE_CONFLICT, False
            )
            _LOGGER.debug(
                "Auto-cancel on pause conflict: %s",
                self._auto_cancel_on_pause_conflict,
            )

    @property
    def name(self) -> str:
        """Return the name of the provider."""
        return "OekoBox Online"

    def supports_pause(self) -> bool:
        """Return whether the provider supports pausing deliveries."""
        # OekoBox Online supports pausing deliveries
        return True

    @staticmethod
    def _parse_date(date_value: date_type | dt | str) -> date_type:
        """Parse a date value to a date object.

        Args:
            date_value: Date value to parse (can be date, datetime, or string)

        Returns:
            date object
        """
        if isinstance(date_value, date_type) and not isinstance(date_value, dt):
            return date_value
        if isinstance(date_value, dt):
            return date_value.date()
        # Parse string
        return dt.strptime(str(date_value), "%Y-%m-%d").date()

    async def _get_shop_dates(self) -> list[ShopDate]:
        """Get all shop dates from the API.

        Returns:
            List of ShopDate objects

        Raises:
            RuntimeError: If not authenticated
        """
        if not self._authenticated or self._client is None:
            if not await self.authenticate():
                raise RuntimeError("Not authenticated with OekoBox Online")

        dates = await self._client.get_dates()
        return [d for d in dates if isinstance(d, ShopDate)]

    async def _get_pauses(self) -> list[Pause]:
        """Get all pauses from the API.

        Returns:
            List of Pause objects

        Raises:
            RuntimeError: If not authenticated
        """
        if not self._authenticated or self._client is None:
            if not await self.authenticate():
                raise RuntimeError("Not authenticated with OekoBox Online")

        dates = await self._client.get_dates()
        return [d for d in dates if isinstance(d, Pause)]

    def _filter_pending_deliveries(
        self, shop_dates: list[ShopDate]
    ) -> list[tuple[date_type, ShopDate]]:
        """Filter and sort pending/active deliveries.

        Args:
            shop_dates: List of ShopDate objects to filter

        Returns:
            List of tuples (date, ShopDate) sorted by date
        """
        now = dt.now().date()
        pending_dates = []

        for shop_date in shop_dates:
            # Filter for pending/in-progress orders (order_state 0 or 1)
            # and dates that are today or in the future
            # Also exclude dates with order_id == 0 (no delivery planned)
            if shop_date.order_state in (0, 1) and shop_date.order_id != 0:
                date_obj = self._parse_date(shop_date.delivery_date)
                if date_obj >= now:
                    pending_dates.append((date_obj, shop_date))

        # Sort by date
        pending_dates.sort(key=lambda x: x[0])
        return pending_dates

    async def _find_next_delivery(self) -> tuple[date_type | None, ShopDate | None]:
        """Find the next pending delivery.

        Returns:
            Tuple of (delivery_date, shop_date) or (None, None) if no delivery found
        """
        shop_dates = await self._get_shop_dates()
        pending_dates = self._filter_pending_deliveries(shop_dates)

        if pending_dates:
            return pending_dates[0]
        return None, None

    def _check_if_paused(self, shop_date: ShopDate | None, pauses: list[Pause]) -> bool:
        """Check if a delivery is paused.

        Args:
            shop_date: The ShopDate to check
            pauses: List of Pause objects from the API

        Returns:
            True if the delivery is paused, False otherwise
        """
        if not shop_date:
            return False

        # Check if ShopDate has is_paused attribute
        if hasattr(shop_date, "is_paused") and shop_date.is_paused:
            return True

        # Check if there's a Pause object matching this delivery
        delivery_date = self._parse_date(shop_date.delivery_date)
        for pause in pauses:
            if hasattr(pause, "delivery_date"):
                pause_date = self._parse_date(pause.delivery_date)
                if pause_date == delivery_date:
                    return True
            # Some implementations might use date_from/date_to
            if hasattr(pause, "date_from") and hasattr(pause, "date_to"):
                date_from = self._parse_date(pause.date_from)
                date_to = self._parse_date(pause.date_to)
                if date_from <= delivery_date <= date_to:
                    return True

        return False

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
            # Find the next delivery
            delivery_date, next_shop_date = await self._find_next_delivery()

            # Get pauses to check if delivery is paused
            pauses = await self._get_pauses()
            is_paused = self._check_if_paused(next_shop_date, pauses)

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

            # Extract last_order_change if available
            last_order_change = None
            if next_shop_date and hasattr(next_shop_date, "last_order_change"):
                last_order_change = next_shop_date.last_order_change

            return DeliveryInfo(
                delivery_date=delivery_datetime,
                items=items,
                last_order_change=last_order_change,
                is_paused=is_paused,
                can_pause=self.supports_pause(),
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

    async def pause_next_delivery(self) -> bool:
        """Pause the next delivery.

        Returns:
            True if successful, False otherwise
        """
        if not self._authenticated or self._client is None:
            if not await self.authenticate():
                _LOGGER.error("Not authenticated, cannot pause delivery")
                return False

        try:
            # Find the next pending delivery
            delivery_date, next_shop_date = await self._find_next_delivery()

            if not next_shop_date or not delivery_date:
                _LOGGER.warning("No pending delivery found to pause")
                return False

            _LOGGER.debug(
                "Attempting to pause delivery on %s (order_id %s)",
                delivery_date,
                next_shop_date.order_id,
            )

            # Use add_pause method with the delivery date
            # The pause needs to span the entire week (Monday to Sunday) for it to show up in the shop UI
            if hasattr(self._client, "add_pause"):
                # Calculate the start (Monday) and end (Sunday) of the week containing the delivery date
                # weekday() returns 0 for Monday, 6 for Sunday
                days_to_monday = delivery_date.weekday()  # 0 if Monday, 6 if Sunday
                week_start = delivery_date - timedelta(days=days_to_monday)
                week_end = week_start + timedelta(days=6)  # Sunday

                # Convert to datetime objects
                from_datetime = dt.combine(week_start, dt.min.time())
                to_datetime = dt.combine(week_end, dt.max.time())

                _LOGGER.debug(
                    "Pausing full week: %s to %s (delivery on %s)",
                    week_start,
                    week_end,
                    delivery_date,
                )

                try:
                    # First attempt without auto_cancel
                    _LOGGER.debug(
                        "Calling add_pause from %s to %s (auto_cancel=False)",
                        week_start,
                        week_end,
                    )
                    await self._client.add_pause(
                        from_datetime, to_datetime, auto_cancel=False
                    )
                    _LOGGER.info(
                        "Successfully paused delivery week %s to %s (delivery on %s, order_id %s)",
                        week_start,
                        week_end,
                        delivery_date,
                        next_shop_date.order_id,
                    )
                    return True

                except OekoboxAPIError as api_err:
                    # Check if it's a HTTP 409 Conflict error
                    if hasattr(api_err, "status_code") and api_err.status_code == 409:
                        _LOGGER.debug(
                            "Received HTTP 409 Conflict when trying to pause delivery week %s to %s: %s",
                            week_start,
                            week_end,
                            api_err,
                        )

                        # Retry with auto_cancel if the option is enabled
                        if self._auto_cancel_on_pause_conflict:
                            _LOGGER.info(
                                "Auto-cancel on pause conflict is enabled, retrying with auto_cancel=True for week %s to %s",
                                week_start,
                                week_end,
                            )
                            try:
                                await self._client.add_pause(
                                    from_datetime, to_datetime, auto_cancel=True
                                )
                                _LOGGER.info(
                                    "Successfully paused delivery week %s to %s with auto_cancel=True (delivery on %s, order_id %s)",
                                    week_start,
                                    week_end,
                                    delivery_date,
                                    next_shop_date.order_id,
                                )
                                return True
                            except Exception as retry_err:
                                _LOGGER.error(
                                    "Failed to pause delivery with auto_cancel=True: %s",
                                    retry_err,
                                )
                                return False
                        else:
                            _LOGGER.warning(
                                "HTTP 409 Conflict: A basket is already planned for the week %s to %s. "
                                "Enable 'Auto-cancel on pause conflict' option to automatically "
                                "cancel the order when pausing.",
                                week_start,
                                week_end,
                            )
                            return False
                    else:
                        # Re-raise if it's not a 409 error
                        raise

            else:
                _LOGGER.warning(
                    "add_pause method not available in pyoekoboxonline library"
                )
                return False
        except Exception as err:
            _LOGGER.error("Failed to pause delivery: %s", err)
            return False

    async def unpause_next_delivery(self) -> bool:
        """Unpause (resume) the next delivery.

        Returns:
            True if successful, False otherwise
        """
        if not self._authenticated or self._client is None:
            if not await self.authenticate():
                _LOGGER.error("Not authenticated, cannot unpause delivery")
                return False

        try:
            # Find the next delivery
            delivery_date, next_shop_date = await self._find_next_delivery()

            if not next_shop_date:
                _LOGGER.warning("No delivery found to unpause")
                return False

            # Get pauses and check if delivery is paused
            pauses = await self._get_pauses()
            if not self._check_if_paused(next_shop_date, pauses):
                _LOGGER.warning(
                    "Delivery on %s is not paused, nothing to unpause", delivery_date
                )
                return False

            # Find the pause ID for this delivery
            pause_id = None
            for pause in pauses:
                if hasattr(pause, "delivery_date"):
                    pause_date = self._parse_date(pause.delivery_date)
                    if pause_date == delivery_date and hasattr(pause, "id"):
                        pause_id = pause.id
                        break
                # Check date range pauses
                elif hasattr(pause, "date_from") and hasattr(pause, "date_to"):
                    date_from = self._parse_date(pause.date_from)
                    date_to = self._parse_date(pause.date_to)
                    if date_from <= delivery_date <= date_to and hasattr(pause, "id"):
                        pause_id = pause.id
                        break

            if pause_id is None:
                _LOGGER.error(
                    "Could not find pause ID for delivery on %s", delivery_date
                )
                return False

            # Use drop_pause method with the pause ID
            if hasattr(self._client, "drop_pause"):
                await self._client.drop_pause(pause_id)
                _LOGGER.info(
                    "Unpaused delivery on %s (pause_id %s, order_id %s)",
                    delivery_date,
                    pause_id,
                    next_shop_date.order_id,
                )
                return True
            else:
                _LOGGER.warning(
                    "drop_pause method not available in pyoekoboxonline library"
                )
                return False
        except Exception as err:
            _LOGGER.error("Failed to unpause delivery: %s", err)
            return False
