"""Data update coordinator for Organic Box integration."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import DeliveryInfo
from .provider import OrganicBoxProvider

_LOGGER = logging.getLogger(__name__)


class OrganicBoxDataUpdateCoordinator(DataUpdateCoordinator[DeliveryInfo]):
    """Class to manage fetching Organic Box data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        provider: OrganicBoxProvider,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            provider: The organic box provider instance
        """
        self.provider = provider

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

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
            return delivery_info
        except Exception as err:
            _LOGGER.error("Error fetching data from provider: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
