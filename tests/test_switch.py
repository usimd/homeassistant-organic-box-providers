"""Test the switch platform."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from pyoekoboxonline.models import ShopDate


@pytest.mark.integration
async def test_switch_setup_with_pause_support(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_client,
    mock_oekobox_online,
) -> None:
    """Test switch is created when provider supports pause."""
    # Mock delivery data
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

    # Check if the switch entity is created
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    switch_entries = [e for e in entries if e.domain == "switch"]

    # Should have one switch entity
    assert len(switch_entries) == 1
    assert "pause" in switch_entries[0].unique_id


@pytest.mark.integration
async def test_switch_pause_delivery(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_client,
    mock_oekobox_online,
) -> None:
    """Test pausing delivery via switch."""
    # Mock delivery data
    shop_date = ShopDate(
        delivery_date=datetime(2025, 11, 15).date(),
        order_id=123,
        order_state=0,
    )
    mock_oekobox_client.get_dates.return_value = [shop_date]
    mock_oekobox_client.get_order_items.return_value = []
    mock_oekobox_client.pause_delivery = AsyncMock()

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Find the switch entity
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    switch_entries = [
        e for e in entries if e.domain == "switch" and "pause" in e.unique_id
    ]

    assert len(switch_entries) == 1
    entity_id = switch_entries[0].entity_id

    # Turn on the switch (pause delivery)
    with patch.object(mock_oekobox_client, "pause_delivery", new_callable=AsyncMock):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()


@pytest.mark.integration
async def test_switch_unpause_delivery(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_client,
    mock_oekobox_online,
) -> None:
    """Test unpausing delivery via switch."""
    # Mock delivery data
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

    # Find the switch entity
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    switch_entries = [
        e for e in entries if e.domain == "switch" and "pause" in e.unique_id
    ]

    assert len(switch_entries) == 1
    entity_id = switch_entries[0].entity_id

    # Turn off the switch (unpause delivery)
    with patch.object(mock_oekobox_client, "unpause_delivery", new_callable=AsyncMock):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            "turn_off",
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()
