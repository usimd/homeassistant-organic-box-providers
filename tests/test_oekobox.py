"""Tests for OekoBox provider implementation."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.organic_box.models import DeliveryInfo
from custom_components.organic_box.oekobox import OekoBoxProvider


@pytest.mark.unit
async def test_oekobox_provider_initialization(hass: HomeAssistant):
    """Test OekoBoxProvider initialization."""
    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")

    assert provider._username == "test@example.com"
    assert provider._password == "password"
    assert provider._shop_id == "shop123"
    assert provider._client is None
    assert provider.is_authenticated is False
    assert provider.name == "OekoBox Online"


@pytest.mark.unit
async def test_oekobox_provider_authenticate_success(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test successful authentication."""
    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    result = await provider.authenticate()

    assert result is True
    assert provider.is_authenticated is True
    mock_oekobox_client.logon.assert_called_once_with(guest=False)


@pytest.mark.unit
async def test_oekobox_provider_authenticate_no_shop_id(hass: HomeAssistant):
    """Test authentication fails without shop_id."""
    provider = OekoBoxProvider(hass, "test@example.com", "password", None)
    result = await provider.authenticate()

    assert result is False
    assert provider.is_authenticated is False


@pytest.mark.unit
async def test_oekobox_provider_authenticate_failure(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test authentication failure."""
    mock_oekobox_client.logon.side_effect = Exception("Auth failed")

    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    result = await provider.authenticate()

    assert result is False
    assert provider.is_authenticated is False


@pytest.mark.unit
async def test_oekobox_provider_test_connection(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test connection test."""
    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    result = await provider.test_connection()

    assert result is True
    assert provider.is_authenticated is True


@pytest.mark.unit
async def test_oekobox_provider_get_next_delivery_empty(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test getting next delivery with no dates."""
    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()

    delivery_info = await provider.get_next_delivery()

    assert isinstance(delivery_info, DeliveryInfo)
    assert delivery_info.delivery_date is None
    assert len(delivery_info.items) == 0


@pytest.mark.unit
async def test_oekobox_provider_get_next_delivery_with_dates(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test getting next delivery with dates."""
    from pyoekoboxonline import DDate

    # Mock DDate object
    mock_ddate = MagicMock(spec=DDate)
    mock_ddate.delivery_date = "2025-11-15"

    mock_oekobox_client.get_dates.return_value = [mock_ddate]

    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()

    delivery_info = await provider.get_next_delivery()

    assert isinstance(delivery_info, DeliveryInfo)
    assert delivery_info.delivery_date is not None
    assert delivery_info.delivery_date.date() == datetime(2025, 11, 15).date()


@pytest.mark.unit
async def test_oekobox_provider_close(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test closing the provider."""
    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()
    await provider.close()

    mock_oekobox_client.close.assert_called_once()
    assert provider._client is None
    assert provider.is_authenticated is False
