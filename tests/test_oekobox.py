"""Tests for OekoBox provider (integration tests - requires actual API or mocking)."""

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

# Add the custom_components directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from organic_box.oekobox import OekoBoxProvider
from organic_box.models import DeliveryInfo


@pytest.mark.asyncio
async def test_oekobox_provider_name():
    """Test OekoBox provider name."""
    provider = OekoBoxProvider("test_user", "test_pass")
    assert provider.name == "OekoBox Online"


@pytest.mark.asyncio
async def test_oekobox_authentication_success():
    """Test successful authentication."""
    with patch("custom_components.organic_box.oekobox.OekoBoxOnline") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        provider = OekoBoxProvider("test_user", "test_pass")
        result = await provider.authenticate()

        assert result is True
        assert provider.is_authenticated
        mock_instance.login.assert_called_once()


@pytest.mark.asyncio
async def test_oekobox_authentication_failure():
    """Test failed authentication."""
    with patch("custom_components.organic_box.oekobox.OekoBoxOnline") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.login.side_effect = Exception("Authentication failed")
        mock_client.return_value = mock_instance

        provider = OekoBoxProvider("test_user", "test_pass")
        result = await provider.authenticate()

        assert result is False
        assert not provider.is_authenticated


@pytest.mark.asyncio
async def test_oekobox_get_next_delivery():
    """Test getting next delivery."""
    mock_delivery_data = {
        "delivery_date": "2025-11-15T10:00:00",
        "items": [
            {
                "name": "Organic Apples",
                "quantity": 2.5,
                "unit": "kg",
                "id": "apple-123",
            },
            {
                "name": "Organic Carrots",
                "quantity": 1.0,
                "unit": "kg",
                "id": "carrot-456",
            },
        ],
    }

    with patch("custom_components.organic_box.oekobox.OekoBoxOnline") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get_next_delivery.return_value = mock_delivery_data
        mock_client.return_value = mock_instance

        provider = OekoBoxProvider("test_user", "test_pass")
        await provider.authenticate()

        delivery = await provider.get_next_delivery()

        assert isinstance(delivery, DeliveryInfo)
        assert delivery.delivery_date is not None
        assert len(delivery.items) == 2
        assert delivery.items[0].name == "Organic Apples"
        assert delivery.items[0].quantity == 2.5
        assert delivery.items[1].name == "Organic Carrots"


@pytest.mark.asyncio
async def test_oekobox_close():
    """Test closing the provider."""
    with patch("custom_components.organic_box.oekobox.OekoBoxOnline") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        provider = OekoBoxProvider("test_user", "test_pass")
        await provider.authenticate()

        assert provider.is_authenticated

        await provider.close()

        assert not provider.is_authenticated
        mock_instance.close.assert_called_once()
