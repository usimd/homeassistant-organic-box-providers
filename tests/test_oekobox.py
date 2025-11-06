"""Tests for OekoBox provider implementation."""

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
    from datetime import date
    from pyoekoboxonline.models import ShopDate

    # Mock ShopDate object with order_state 0 (pending)
    mock_shop_date = MagicMock(spec=ShopDate)
    mock_shop_date.order_state = 0  # pending
    mock_shop_date.delivery_date = date(2025, 11, 15)
    mock_shop_date.order_id = 123

    mock_oekobox_client.get_dates.return_value = [mock_shop_date]
    mock_oekobox_client.get_order_items.return_value = []

    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()

    delivery_info = await provider.get_next_delivery()

    assert isinstance(delivery_info, DeliveryInfo)
    assert delivery_info.delivery_date is not None
    assert delivery_info.delivery_date.date() == date(2025, 11, 15)


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


@pytest.mark.unit
async def test_oekobox_provider_get_next_delivery_filters_done_orders(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test that done orders (order_state=2) are filtered out."""
    from datetime import date, timedelta
    from pyoekoboxonline.models import ShopDate

    # Mock ShopDate objects: one done (order_state=2), one pending (order_state=0)
    future_date = date.today() + timedelta(days=7)

    mock_done_date = MagicMock(spec=ShopDate)
    mock_done_date.order_state = 2  # done
    mock_done_date.delivery_date = date.today() - timedelta(days=1)
    mock_done_date.order_id = 100

    mock_pending_date = MagicMock(spec=ShopDate)
    mock_pending_date.order_state = 0  # pending
    mock_pending_date.delivery_date = future_date
    mock_pending_date.order_id = 101

    mock_oekobox_client.get_dates.return_value = [mock_done_date, mock_pending_date]
    mock_oekobox_client.get_order_items.return_value = []

    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()

    delivery_info = await provider.get_next_delivery()

    assert isinstance(delivery_info, DeliveryInfo)
    assert delivery_info.delivery_date is not None
    assert delivery_info.delivery_date.date() == future_date


@pytest.mark.unit
async def test_oekobox_provider_get_next_delivery_filters_cancelled_orders(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test that cancelled orders (order_state=-1) are filtered out."""
    from datetime import date, timedelta
    from pyoekoboxonline.models import ShopDate

    future_date = date.today() + timedelta(days=7)

    mock_cancelled_date = MagicMock(spec=ShopDate)
    mock_cancelled_date.order_state = -1  # cancelled
    mock_cancelled_date.delivery_date = future_date
    mock_cancelled_date.order_id = 100

    mock_in_progress_date = MagicMock(spec=ShopDate)
    mock_in_progress_date.order_state = 1  # in preparation/delivery
    mock_in_progress_date.delivery_date = future_date + timedelta(days=1)
    mock_in_progress_date.order_id = 101

    mock_oekobox_client.get_dates.return_value = [
        mock_cancelled_date,
        mock_in_progress_date,
    ]
    mock_oekobox_client.get_order_items.return_value = []

    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()

    delivery_info = await provider.get_next_delivery()

    assert isinstance(delivery_info, DeliveryInfo)
    assert delivery_info.delivery_date is not None
    assert delivery_info.delivery_date.date() == future_date + timedelta(days=1)


@pytest.mark.unit
async def test_oekobox_provider_get_next_delivery_with_items(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test getting next delivery with order items."""
    from datetime import date, timedelta
    from pyoekoboxonline.models import ShopDate

    future_date = date.today() + timedelta(days=7)

    mock_shop_date = MagicMock(spec=ShopDate)
    mock_shop_date.order_state = 0  # pending
    mock_shop_date.delivery_date = future_date
    mock_shop_date.order_id = 123

    # Mock Item object
    mock_item = MagicMock()
    mock_item.item_id = 456
    mock_item.name = "Apples"
    mock_item.unit = "kg"
    mock_item.amount_def = 2.0

    mock_oekobox_client.get_dates.return_value = [mock_shop_date]
    mock_oekobox_client.get_order_items.return_value = [mock_item]

    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()

    delivery_info = await provider.get_next_delivery()

    assert isinstance(delivery_info, DeliveryInfo)
    assert delivery_info.delivery_date is not None
    assert len(delivery_info.items) == 1
    assert delivery_info.items[0].name == "Apples"
    assert delivery_info.items[0].quantity == 2.0
    assert delivery_info.items[0].unit == "kg"
    assert delivery_info.items[0].product_id == "456"


@pytest.mark.unit
async def test_oekobox_provider_get_next_delivery_filters_no_delivery_planned(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test that dates with order_id=0 (no delivery planned) are filtered out."""
    from datetime import date, timedelta
    from pyoekoboxonline.models import ShopDate

    future_date = date.today() + timedelta(days=7)

    # Mock ShopDate with order_id=0 (no delivery planned)
    mock_no_delivery_date = MagicMock(spec=ShopDate)
    mock_no_delivery_date.order_state = 0  # pending
    mock_no_delivery_date.delivery_date = future_date
    mock_no_delivery_date.order_id = 0  # No delivery planned

    # Mock ShopDate with actual delivery
    mock_delivery_date = MagicMock(spec=ShopDate)
    mock_delivery_date.order_state = 0  # pending
    mock_delivery_date.delivery_date = future_date + timedelta(days=1)
    mock_delivery_date.order_id = 123  # Actual delivery

    mock_oekobox_client.get_dates.return_value = [
        mock_no_delivery_date,
        mock_delivery_date,
    ]
    mock_oekobox_client.get_order_items.return_value = []

    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()

    delivery_info = await provider.get_next_delivery()

    assert isinstance(delivery_info, DeliveryInfo)
    assert delivery_info.delivery_date is not None
    # Should return the date with order_id=123, not the one with order_id=0
    assert delivery_info.delivery_date.date() == future_date + timedelta(days=1)


@pytest.mark.unit
async def test_oekobox_provider_get_next_delivery_with_xunit_override(
    hass: HomeAssistant,
    mock_oekobox_client,
    mock_oekobox_online,
):
    """Test that XUnit objects override Item unit and quantity."""
    from datetime import date, timedelta
    from pyoekoboxonline.models import ShopDate, XUnit

    future_date = date.today() + timedelta(days=7)

    mock_shop_date = MagicMock(spec=ShopDate)
    mock_shop_date.order_state = 0  # pending
    mock_shop_date.delivery_date = future_date
    mock_shop_date.order_id = 123

    # Mock Item object
    mock_item = MagicMock()
    mock_item.item_id = 456
    mock_item.name = "Potatoes"
    mock_item.unit = "kg"
    mock_item.amount_def = 1.0

    # Mock XUnit object that overrides the unit and quantity
    mock_xunit = MagicMock(spec=XUnit)
    mock_xunit.item_id = 456  # References the same item
    mock_xunit.name = "bag"  # Override unit
    mock_xunit.parts = "3.5"  # Override quantity

    mock_oekobox_client.get_dates.return_value = [mock_shop_date]
    # XUnit comes before or after Item in the list
    mock_oekobox_client.get_order_items.return_value = [mock_item, mock_xunit]

    provider = OekoBoxProvider(hass, "test@example.com", "password", "shop123")
    await provider.authenticate()

    delivery_info = await provider.get_next_delivery()

    assert isinstance(delivery_info, DeliveryInfo)
    assert len(delivery_info.items) == 1
    assert delivery_info.items[0].name == "Potatoes"
    # XUnit should override the unit and quantity
    assert delivery_info.items[0].unit == "bag"
    assert delivery_info.items[0].quantity == 3.5
    assert delivery_info.items[0].product_id == "456"
