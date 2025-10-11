
"""Organic Box Home Assistant Integration."""

import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import service
from .const import DOMAIN
from .amperhof import AmperhofProvider

SCAN_INTERVAL = timedelta(hours=1)
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Organic Box integration."""
    hass.data.setdefault(DOMAIN, {})

    async def update_basket_service(call):
        await async_update_basket(hass)

    async def align_shopping_list_service(call):
        await async_align_shopping_list(hass)

    hass.services.async_register(DOMAIN, "update_basket", update_basket_service)
    hass.services.async_register(DOMAIN, "align_shopping_list", align_shopping_list_service)

    async_track_time_interval(hass, lambda now: hass.async_create_task(async_update_basket(hass)), SCAN_INTERVAL)
    return True

async def async_update_basket(hass: HomeAssistant):
    # Example: Only Amperhof for now, extend for other providers
    config = hass.data[DOMAIN].get("config", {})
    provider = AmperhofProvider(config.get("amperhof", {}))
    delivery = await provider.async_get_next_delivery()
    hass.data[DOMAIN]["delivery"] = delivery
    _LOGGER.info("Organic Box basket updated.")

async def async_align_shopping_list(hass: HomeAssistant):
    # Align planned basket with Home Assistant's To Do list (shopping_list)
    delivery = hass.data[DOMAIN].get("delivery")
    if not delivery:
        _LOGGER.warning("No delivery data available to align shopping list.")
        return
    basket_items = {item.name.lower() for item in delivery.basket.items}
    # Get shopping_list entity (Home Assistant's To Do list)
    todo_entity_id = "todo.shopping_list"
    state_obj = hass.states.get(todo_entity_id)
    if not state_obj:
        _LOGGER.warning("Shopping list entity not found.")
        return
    todo_items = state_obj.attributes.get("items", [])
    # Remove items from To Do list that are present in the basket
    items_to_remove = [item for item in todo_items if item.get("name", "").lower() in basket_items]
    for item in items_to_remove:
        await hass.services.async_call("todo", "remove_item", {"entity_id": todo_entity_id, "item": item["name"]})
    _LOGGER.info(f"Removed {len(items_to_remove)} items from shopping list.")
