"""Tests for OekoBox provider (integration tests - requires actual API or mocking)."""

import pytest
from unittest.mock import AsyncMock, patch

from custom_components.organic_box.oekobox import OekoBoxProvider
from custom_components.organic_box.models import DeliveryInfo


@pytest.mark.asyncio
async def test_oekobox_provider_name():
    """Test OekoBox provider name."""
    provider = OekoBoxProvider("test_user", "test_pass", shop_id="test_shop")
    assert provider.name == "OekoBox Online"


@pytest.mark.asyncio
async def test_oekobox_authentication_success():
    """Test successful authentication."""
    with patch("custom_components.organic_box.oekobox.OekoBoxOnline") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.logon.return_value = {"status": "ok"}

        provider = OekoBoxProvider("test_user", "test_pass", shop_id="test_shop")
        result = await provider.authenticate()

        assert result is True
        assert provider.is_authenticated
        mock_client.assert_called_once_with(
            shop_id="test_shop", username="test_user", password="test_pass"
        )
        mock_instance.logon.assert_called_once_with(guest=False)


@pytest.mark.asyncio
async def test_oekobox_authentication_failure():
    """Test failed authentication."""
    with patch("custom_components.organic_box.oekobox.OekoBoxOnline") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.logon.side_effect = Exception("Authentication failed")
        mock_client.return_value = mock_instance

        provider = OekoBoxProvider("test_user", "test_pass", shop_id="test_shop")
        result = await provider.authenticate()

        assert result is False
        assert not provider.is_authenticated


@pytest.mark.asyncio
async def test_oekobox_get_next_delivery():
    """Test getting next delivery."""
    from unittest.mock import MagicMock

    # Mock DDate and Order objects
    mock_ddate = MagicMock()
    mock_ddate.delivery_date = "2025-11-15"
    mock_ddate.id = 1

    mock_order = MagicMock()
    mock_order.ddate = "2025-11-15"
    mock_order.id = 123

    mock_order_item1 = MagicMock()
    mock_order_item1.item_id = 1
    mock_order_item1.amount = 2.5
    mock_order_item1.unit = "kg"

    mock_order_item2 = MagicMock()
    mock_order_item2.item_id = 2
    mock_order_item2.amount = 1.0
    mock_order_item2.unit = "kg"

    mock_item1 = MagicMock()
    mock_item1.name = "Organic Apples"

    mock_item2 = MagicMock()
    mock_item2.name = "Organic Carrots"

    with patch("custom_components.organic_box.oekobox.OekoBoxOnline") as mock_client:
        with patch("custom_components.organic_box.oekobox.DDate") as MockDDate:
            with patch("custom_components.organic_box.oekobox.Order") as MockOrder:
                mock_instance = AsyncMock()
                mock_instance.get_dates.return_value = [mock_ddate]
                mock_instance.get_orders.return_value = [mock_order]
                mock_instance.get_order_items.return_value = [
                    mock_order_item1,
                    mock_order_item2,
                ]
                mock_instance.get_item.side_effect = [mock_item1, mock_item2]
                mock_instance.logon.return_value = {"status": "ok"}
                mock_client.return_value = mock_instance

                # Make isinstance checks work
                MockDDate.return_value = mock_ddate
                MockOrder.return_value = mock_order

                provider = OekoBoxProvider(
                    "test_user", "test_pass", shop_id="test_shop"
                )
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
        mock_instance.logon.return_value = {"status": "ok"}
        mock_client.return_value = mock_instance

        provider = OekoBoxProvider("test_user", "test_pass", shop_id="test_shop")
        await provider.authenticate()

        assert provider.is_authenticated

        await provider.close()

        assert not provider.is_authenticated
        mock_instance.close.assert_called_once()
