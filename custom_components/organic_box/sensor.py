"""Organic Box sensor platform for Home Assistant integration."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


async def async_setup_platform(
    hass: HomeAssistant,
    # config: ConfigType,
    # async_add_entities: callable,
    # discovery_info: dict | None = None,
) -> None:
    """Set up Organic Box sensor platform."""
    deliveries = hass.data[DOMAIN].get("deliveries", [])
    entities = []
    for delivery in deliveries:
        entities.append(OrganicBoxDeliverySensor(delivery))
        entities.append(OrganicBoxBasketSensor(delivery))

    def async_add_entities(entities: list) -> None:
        pass  # Dummy for ruff compliance

    async_add_entities(entities)


class OrganicBoxDeliverySensor(Entity):
    """Sensor for Organic Box delivery date."""

    def __init__(self, delivery: object) -> None:
        """Initialize delivery sensor."""
        self._delivery = delivery
        self._attr_name = f"Organic Box Delivery Date ({delivery.date})"

    @property
    def state(self) -> str:
        """Return delivery date."""
        return self._delivery.date

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes for delivery sensor."""
        return {
            "address": getattr(self._delivery, "address", None),
            "basket_id": self._delivery.basket.id,
        }


class OrganicBoxBasketSensor(Entity):
    """Sensor for Organic Box basket contents."""

    def __init__(self, delivery: object) -> None:
        """Initialize basket sensor."""
        self._delivery = delivery
        self._attr_name = f"Organic Box Basket ({delivery.date})"

    @property
    def state(self) -> int:
        """Return number of items in basket."""
        return len(self._delivery.basket.items)

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes for basket sensor."""
        return {
            "items": [
                {
                    "name": item.name,
                    "amount": item.amount,
                    "unit": item.unit,
                    "price": item.price.amount,
                }
                for item in self._delivery.basket.items
            ],
            "total_price": self._delivery.basket.total_price.amount,
        }
