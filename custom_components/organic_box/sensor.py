
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities, discovery_info=None):
    delivery = hass.data[DOMAIN].get("delivery")
    entities = []
    if delivery:
        entities.append(OrganicBoxDeliverySensor(delivery))
        entities.append(OrganicBoxBasketSensor(delivery))
    async_add_entities(entities)

class OrganicBoxDeliverySensor(Entity):
    def __init__(self, delivery):
        self._delivery = delivery
        self._attr_name = "Organic Box Next Delivery Date"

    @property
    def state(self):
        return self._delivery.date

    @property
    def extra_state_attributes(self):
        return {
            "address": self._delivery.address
        }

class OrganicBoxBasketSensor(Entity):
    def __init__(self, delivery):
        self._delivery = delivery
        self._attr_name = "Organic Box Planned Basket"

    @property
    def state(self):
        return len(self._delivery.basket.items)

    @property
    def extra_state_attributes(self):
        return {
            "items": [
                {
                    "name": item.name,
                    "amount": item.amount,
                    "unit": item.unit,
                    "price": item.price.amount,
                    "category": item.category,
                    "image_url": item.image_url
                }
                for item in self._delivery.basket.items
            ],
            "total_price": self._delivery.basket.total_price.amount
        }
