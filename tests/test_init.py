"""Test the organic_box __init__.py setup/unload."""

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.organic_box.const import DOMAIN


@pytest.mark.integration
async def test_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_online,
) -> None:
    """Test successful setup of a config entry."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert result is True
    assert mock_config_entry.state == config_entries.ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


@pytest.mark.integration
async def test_setup_entry_auth_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_client,
    mock_oekobox_online,
) -> None:
    """Test setup fails when authentication fails."""
    mock_config_entry.add_to_hass(hass)
    mock_oekobox_client.logon.side_effect = Exception("Auth failed")

    result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert result is False
    assert mock_config_entry.state == config_entries.ConfigEntryState.SETUP_RETRY


@pytest.mark.integration
async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_client,
    mock_oekobox_online,
) -> None:
    """Test unloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == config_entries.ConfigEntryState.LOADED

    result = await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert result is True
    assert mock_config_entry.state == config_entries.ConfigEntryState.NOT_LOADED
    mock_oekobox_client.close.assert_called_once()


@pytest.mark.integration
async def test_reload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_oekobox_client,
    mock_oekobox_online,
) -> None:
    """Test reloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == config_entries.ConfigEntryState.LOADED

    result = await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert result is True
    assert mock_config_entry.state == config_entries.ConfigEntryState.LOADED
    # Close should be called at least once during unload
    assert mock_oekobox_client.close.call_count >= 1
