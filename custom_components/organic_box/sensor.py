"""Sensor platform for Organic Box integration."""

from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_BASKET_ITEMS, ATTR_PROVIDER, DOMAIN
from .coordinator import OrganicBoxDataUpdateCoordinator
from .models import DeliveryInfo

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Organic Box sensors from a config entry."""
    coordinator: OrganicBoxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            OrganicBoxNextDeliverySensor(coordinator, entry),
            OrganicBoxBasketItemsSensor(coordinator, entry),
        ]
    )


class OrganicBoxSensorBase(
    CoordinatorEntity[OrganicBoxDataUpdateCoordinator], SensorEntity
):
    """Base class for Organic Box sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OrganicBoxDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data update coordinator
            entry: The config entry
        """
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Organic Box - {entry.data[CONF_USERNAME]}",
            manufacturer=coordinator.provider.name,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def delivery_info(self) -> DeliveryInfo:
        """Return the delivery info from coordinator data."""
        return self.coordinator.data


class OrganicBoxNextDeliverySensor(OrganicBoxSensorBase):
    """Sensor for the next delivery date."""

    _attr_translation_key = "next_delivery"

    def __init__(
        self,
        coordinator: OrganicBoxDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the next delivery sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next_delivery"
        self._attr_icon = "mdi:truck-delivery"

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor."""
        if self.delivery_info and self.delivery_info.delivery_date:
            return self.delivery_info.delivery_date
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.delivery_info:
            return {}

        return {
            ATTR_PROVIDER: self.coordinator.provider.name,
            "total_items": self.delivery_info.total_items,
        }


class OrganicBoxBasketItemsSensor(OrganicBoxSensorBase):
    """Sensor for the basket items count."""

    _attr_translation_key = "basket_items"

    def __init__(
        self,
        coordinator: OrganicBoxDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the basket items sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_basket_items"
        self._attr_icon = "mdi:basket"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "items"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        if self.delivery_info:
            return self.delivery_info.total_items
        return 0

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.delivery_info or not self.delivery_info.items:
            return {}

        items_list = []
        for item in self.delivery_info.items:
            item_dict = {
                "name": item.name,
                "quantity": item.quantity,
            }
            if item.unit:
                item_dict["unit"] = item.unit
            items_list.append(item_dict)

        return {
            ATTR_PROVIDER: self.coordinator.provider.name,
            ATTR_BASKET_ITEMS: items_list,
        }
