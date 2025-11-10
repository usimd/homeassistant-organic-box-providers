"""Test HTTP 409 conflict handling for pause functionality."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from pyoekoboxonline.exceptions import OekoboxAPIError
from pyoekoboxonline.models import ShopDate

from custom_components.organic_box.const import (
    CONF_AUTO_CANCEL_ON_PAUSE_CONFLICT,
    CONF_PASSWORD,
    CONF_PROVIDER,
    CONF_SHOP_ID,
    CONF_USERNAME,
    DOMAIN,
    PROVIDER_OEKOBOX,
)
from custom_components.organic_box.oekobox import OekoBoxProvider


@pytest.fixture
def mock_config_entry_with_auto_cancel():
    """Create a mock config entry with auto_cancel enabled."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PROVIDER: PROVIDER_OEKOBOX,
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_pass",
            CONF_SHOP_ID: "test_shop",
        },
        options={
            CONF_AUTO_CANCEL_ON_PAUSE_CONFLICT: True,
        },
        entry_id="test_entry_auto_cancel",
    )


@pytest.fixture
def mock_config_entry_without_auto_cancel():
    """Create a mock config entry without auto_cancel."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PROVIDER: PROVIDER_OEKOBOX,
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_pass",
            CONF_SHOP_ID: "test_shop",
        },
        options={
            CONF_AUTO_CANCEL_ON_PAUSE_CONFLICT: False,
        },
        entry_id="test_entry_no_auto_cancel",
    )


@pytest.mark.asyncio
async def test_pause_conflict_with_auto_cancel_enabled(
    hass: HomeAssistant,
    mock_config_entry_with_auto_cancel: MockConfigEntry,
) -> None:
    """Test that HTTP 409 conflict triggers retry with auto_cancel=True when enabled."""
    # Create provider with auto_cancel enabled
    provider = OekoBoxProvider(
        hass,
        "test_user",
        "test_pass",
        "test_shop",
        mock_config_entry_with_auto_cancel,
    )

    # Mock the client
    mock_client = AsyncMock()
    provider._client = mock_client
    provider._authenticated = True

    # Mock get_dates to return a shop date
    shop_date = ShopDate(
        delivery_date=datetime(2025, 11, 15).date(),
        order_id=123,
        order_state=0,
    )
    mock_client.get_dates.return_value = [shop_date]

    # First call to add_pause raises HTTP 409 Conflict
    conflict_error = OekoboxAPIError("Conflict", status_code=409)

    # Set up the mock to fail on first call, succeed on second
    mock_client.add_pause = AsyncMock(side_effect=[conflict_error, None])

    # Call pause_next_delivery
    result = await provider.pause_next_delivery()

    # Should succeed after retry
    assert result is True

    # Verify add_pause was called twice
    assert mock_client.add_pause.call_count == 2

    # First call should be with auto_cancel=False
    first_call = mock_client.add_pause.call_args_list[0]
    assert first_call.kwargs.get("auto_cancel") is False

    # Second call should be with auto_cancel=True
    second_call = mock_client.add_pause.call_args_list[1]
    assert second_call.kwargs.get("auto_cancel") is True


@pytest.mark.asyncio
async def test_pause_conflict_without_auto_cancel(
    hass: HomeAssistant,
    mock_config_entry_without_auto_cancel: MockConfigEntry,
) -> None:
    """Test that HTTP 409 conflict returns False when auto_cancel is disabled."""
    # Create provider without auto_cancel
    provider = OekoBoxProvider(
        hass,
        "test_user",
        "test_pass",
        "test_shop",
        mock_config_entry_without_auto_cancel,
    )

    # Mock the client
    mock_client = AsyncMock()
    provider._client = mock_client
    provider._authenticated = True

    # Mock get_dates to return a shop date
    shop_date = ShopDate(
        delivery_date=datetime(2025, 11, 15).date(),
        order_id=123,
        order_state=0,
    )
    mock_client.get_dates.return_value = [shop_date]

    # add_pause raises HTTP 409 Conflict
    conflict_error = OekoboxAPIError("Conflict", status_code=409)
    mock_client.add_pause = AsyncMock(side_effect=conflict_error)

    # Call pause_next_delivery
    result = await provider.pause_next_delivery()

    # Should fail without retry
    assert result is False

    # Verify add_pause was only called once
    assert mock_client.add_pause.call_count == 1

    # Call should be with auto_cancel=False
    call_args = mock_client.add_pause.call_args
    assert call_args.kwargs.get("auto_cancel") is False


@pytest.mark.asyncio
async def test_pause_success_without_conflict(
    hass: HomeAssistant,
    mock_config_entry_with_auto_cancel: MockConfigEntry,
) -> None:
    """Test that successful pause doesn't trigger retry logic."""
    # Create provider with auto_cancel enabled
    provider = OekoBoxProvider(
        hass,
        "test_user",
        "test_pass",
        "test_shop",
        mock_config_entry_with_auto_cancel,
    )

    # Mock the client
    mock_client = AsyncMock()
    provider._client = mock_client
    provider._authenticated = True

    # Mock get_dates to return a shop date
    shop_date = ShopDate(
        delivery_date=datetime(2025, 11, 15).date(),
        order_id=123,
        order_state=0,
    )
    mock_client.get_dates.return_value = [shop_date]

    # add_pause succeeds on first try
    mock_client.add_pause = AsyncMock(return_value=None)

    # Call pause_next_delivery
    result = await provider.pause_next_delivery()

    # Should succeed
    assert result is True

    # Verify add_pause was only called once
    assert mock_client.add_pause.call_count == 1

    # Call should be with auto_cancel=False
    call_args = mock_client.add_pause.call_args
    assert call_args.kwargs.get("auto_cancel") is False


@pytest.mark.asyncio
async def test_pause_conflict_retry_fails(
    hass: HomeAssistant,
    mock_config_entry_with_auto_cancel: MockConfigEntry,
) -> None:
    """Test that failure on retry with auto_cancel=True returns False."""
    # Create provider with auto_cancel enabled
    provider = OekoBoxProvider(
        hass,
        "test_user",
        "test_pass",
        "test_shop",
        mock_config_entry_with_auto_cancel,
    )

    # Mock the client
    mock_client = AsyncMock()
    provider._client = mock_client
    provider._authenticated = True

    # Mock get_dates to return a shop date
    shop_date = ShopDate(
        delivery_date=datetime(2025, 11, 15).date(),
        order_id=123,
        order_state=0,
    )
    mock_client.get_dates.return_value = [shop_date]

    # Both calls to add_pause fail
    conflict_error = OekoboxAPIError("Conflict", status_code=409)
    another_error = OekoboxAPIError("Another error", status_code=500)

    mock_client.add_pause = AsyncMock(side_effect=[conflict_error, another_error])

    # Call pause_next_delivery
    result = await provider.pause_next_delivery()

    # Should fail
    assert result is False

    # Verify add_pause was called twice
    assert mock_client.add_pause.call_count == 2


@pytest.mark.asyncio
async def test_pause_non_409_error(
    hass: HomeAssistant,
    mock_config_entry_with_auto_cancel: MockConfigEntry,
) -> None:
    """Test that non-409 errors don't trigger retry logic."""
    # Create provider with auto_cancel enabled
    provider = OekoBoxProvider(
        hass,
        "test_user",
        "test_pass",
        "test_shop",
        mock_config_entry_with_auto_cancel,
    )

    # Mock the client
    mock_client = AsyncMock()
    provider._client = mock_client
    provider._authenticated = True

    # Mock get_dates to return a shop date
    shop_date = ShopDate(
        delivery_date=datetime(2025, 11, 15).date(),
        order_id=123,
        order_state=0,
    )
    mock_client.get_dates.return_value = [shop_date]

    # add_pause raises a different error (not 409)
    other_error = OekoboxAPIError("Server error", status_code=500)
    mock_client.add_pause = AsyncMock(side_effect=other_error)

    # Call pause_next_delivery
    result = await provider.pause_next_delivery()

    # Should fail
    assert result is False

    # Verify add_pause was only called once (no retry for non-409 errors)
    assert mock_client.add_pause.call_count == 1


@pytest.mark.asyncio
async def test_provider_initialization_with_config_entry(
    hass: HomeAssistant,
    mock_config_entry_with_auto_cancel: MockConfigEntry,
) -> None:
    """Test that provider correctly initializes auto_cancel option from config entry."""
    # Create provider with config entry that has auto_cancel enabled
    provider = OekoBoxProvider(
        hass,
        "test_user",
        "test_pass",
        "test_shop",
        mock_config_entry_with_auto_cancel,
    )

    # Verify the option is loaded
    assert provider._auto_cancel_on_pause_conflict is True


@pytest.mark.asyncio
async def test_provider_initialization_without_config_entry(
    hass: HomeAssistant,
) -> None:
    """Test that provider defaults auto_cancel to False when no config entry."""
    # Create provider without config entry
    provider = OekoBoxProvider(
        hass,
        "test_user",
        "test_pass",
        "test_shop",
        None,  # No config entry
    )

    # Verify the option defaults to False
    assert provider._auto_cancel_on_pause_conflict is False
