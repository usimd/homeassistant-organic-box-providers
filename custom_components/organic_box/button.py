"""Button platform for Organic Box integration."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OrganicBoxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Organic Box buttons from a config entry."""
    coordinator: OrganicBoxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.provider.supports_pause():
        async_add_entities([OrganicBoxPauseDeliveryButton(coordinator, entry)])


class OrganicBoxPauseDeliveryButton(
    CoordinatorEntity[OrganicBoxDataUpdateCoordinator], ButtonEntity
):
    """One-shot button to pause the next delivery."""

    _attr_has_entity_name = True
    _attr_translation_key = "pause_delivery"
    _attr_icon = "mdi:pause-circle"

    def __init__(
        self,
        coordinator: OrganicBoxDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_pause_delivery"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Organic Box - {entry.data[CONF_USERNAME]}",
            manufacturer=coordinator.provider.name,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.can_pause
            and not self.coordinator.data.is_paused
        )

    async def async_press(self) -> None:
        """Pause the next delivery."""
        _LOGGER.debug("Pausing next delivery")
        success = await self.coordinator.provider.pause_next_delivery()
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to pause delivery")
