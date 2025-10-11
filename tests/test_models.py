"""Tests for organic_box models."""

import sys
import types

from custom_components.organic_box.models import Basket, Delivery, Item, Price

# Setup Home Assistant mocks
homeassistant_mod = types.ModuleType("homeassistant")
homeassistant_core_mod = types.ModuleType("homeassistant.core")
homeassistant_core_mod.HomeAssistant = type("HomeAssistant", (), {})
homeassistant_helpers_mod = types.ModuleType("homeassistant.helpers")
homeassistant_helpers_mod.service = None
homeassistant_helpers_typing_mod = types.ModuleType("homeassistant.helpers.typing")
homeassistant_helpers_typing_mod.ConfigType = dict
event_mod = types.ModuleType("homeassistant.helpers.event")


def async_track_time_interval(*args: object, **kwargs: object) -> None:
    """Mock async_track_time_interval."""
    pass


event_mod.async_track_time_interval = async_track_time_interval
sys.modules["homeassistant"] = homeassistant_mod
sys.modules["homeassistant.core"] = homeassistant_core_mod
sys.modules["homeassistant.helpers"] = homeassistant_helpers_mod
sys.modules["homeassistant.helpers.event"] = event_mod
sys.modules["homeassistant.helpers.typing"] = homeassistant_helpers_typing_mod


# Constants for test values
TEST_AMOUNT = 5.0
TEST_CURRENCY = "EUR"
TEST_ITEM_PRICE = 2.5
TEST_BASKET_PRICE = 10.0
TEST_DELIVERY_DATE = "2025-10-16"


def test_price() -> None:
    """Test Price model."""
    p = Price(amount=TEST_AMOUNT)
    assert p.amount == TEST_AMOUNT
    assert p.currency == TEST_CURRENCY


def test_item() -> None:
    """Test Item model."""
    price = Price(amount=TEST_ITEM_PRICE)
    item = Item(
        id="1",
        name="Apple",
        amount=1,
        unit="kg",
        price=price,
        category="Fruit",
    )
    assert item.name == "Apple"
    assert item.price.amount == TEST_ITEM_PRICE


def test_basket() -> None:
    """Test Basket model."""
    price = Price(amount=TEST_BASKET_PRICE)
    items = [
        Item(
            id="1",
            name="Apple",
            amount=1,
            unit="kg",
            price=price,
            category="Fruit",
        ),
    ]
    basket = Basket(items=items, total_price=price)
    assert len(basket.items) == 1
    assert basket.total_price.amount == TEST_BASKET_PRICE


def test_delivery() -> None:
    """Test Delivery model."""
    price = Price(amount=TEST_BASKET_PRICE)
    items = [
        Item(
            id="1",
            name="Apple",
            amount=1,
            unit="kg",
            price=price,
            category="Fruit",
        ),
    ]
    basket = Basket(items=items, total_price=price)
    delivery = Delivery(date=TEST_DELIVERY_DATE, basket=basket)
    assert delivery.date == TEST_DELIVERY_DATE
    assert delivery.basket.total_price.amount == TEST_BASKET_PRICE
