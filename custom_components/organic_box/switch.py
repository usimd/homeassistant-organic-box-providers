"""Switch platform for Organic Box integration."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OrganicBoxDataUpdateCoordinator
from .models import DeliveryInfo

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Organic Box switches from a config entry."""
    coordinator: OrganicBoxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Only add the switch if the provider supports pausing
    if coordinator.provider.supports_pause():
        async_add_entities([OrganicBoxDeliveryPauseSwitch(coordinator, entry)])
    else:
        _LOGGER.debug(
            "Provider %s does not support pausing, switch not created",
            coordinator.provider.name,
        )


class OrganicBoxDeliveryPauseSwitch(
    CoordinatorEntity[OrganicBoxDataUpdateCoordinator], SwitchEntity
):
    """Switch to pause/unpause the next delivery."""

    _attr_has_entity_name = True
    _attr_translation_key = "delivery_pause"

    def __init__(
        self,
        coordinator: OrganicBoxDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch.

        Args:
            coordinator: The data update coordinator
            entry: The config entry
        """
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_delivery_pause"
        self._attr_icon = "mdi:pause-circle"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Organic Box - {entry.data[CONF_USERNAME]}",
            manufacturer=coordinator.provider.name,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def delivery_info(self) -> DeliveryInfo | None:
        """Return the delivery info from coordinator data."""
        return self.coordinator.data

    @property
    def is_on(self) -> bool:
        """Return true if the delivery is paused."""
        if self.delivery_info:
            return self.delivery_info.is_paused
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Only available if there's delivery info and the provider supports pausing
        return (
            self.coordinator.last_update_success
            and self.delivery_info is not None
            and self.delivery_info.can_pause
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Pause the next delivery."""
        _LOGGER.debug("Pausing next delivery")
        success = await self.coordinator.provider.pause_next_delivery()

        if success:
            # Request a data refresh to update the state
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to pause delivery")

    async def async_turn_off(self, **kwargs) -> None:
        """Unpause (resume) the next delivery."""
        _LOGGER.debug("Unpausing next delivery")
        success = await self.coordinator.provider.unpause_next_delivery()

        if success:
            # Request a data refresh to update the state
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to unpause delivery")

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.delivery_info:
            return {}

        attributes = {}
        if self.delivery_info.delivery_date:
            attributes["next_delivery_date"] = (
                self.delivery_info.delivery_date.isoformat()
            )

        return attributes
