"""Test the button platform."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pyoekoboxonline.models import ShopDate
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.integration
async def test_button_setup_with_pause_support(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_client,
    mock_oekobox_online,
) -> None:
    """Test button is created when provider supports pause."""
    shop_date = ShopDate(
        delivery_date=datetime(2025, 11, 15).date(),
        order_id=123,
        order_state=0,
    )
    mock_oekobox_client.get_dates.return_value = [shop_date]
    mock_oekobox_client.get_order_items.return_value = []

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    button_entries = [e for e in entries if e.domain == "button"]

    assert len(button_entries) == 1
    assert "pause" in button_entries[0].unique_id


@pytest.mark.integration
async def test_button_pause_delivery(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_client,
    mock_oekobox_online,
) -> None:
    """Test pausing delivery via button press."""
    shop_date = ShopDate(
        delivery_date=datetime(2025, 11, 15).date(),
        order_id=123,
        order_state=0,
    )
    mock_oekobox_client.get_dates.return_value = [shop_date]
    mock_oekobox_client.get_order_items.return_value = []

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    button_entries = [e for e in entries if e.domain == "button" and "pause" in e.unique_id]

    assert len(button_entries) == 1
    entity_id = button_entries[0].entity_id

    with patch(
        "custom_components.organic_box.oekobox.OekoBoxProvider.pause_next_delivery",
        new_callable=AsyncMock,
        return_value=True,
    ):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            "press",
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()
