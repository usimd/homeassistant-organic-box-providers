"""Tests for organic_box models."""

from datetime import datetime

import pytest

from custom_components.organic_box.models import BasketItem, DeliveryInfo


@pytest.mark.unit
def test_basket_item_creation():
    """Test creating a BasketItem."""
    item = BasketItem(name="Apples", quantity=5.0, unit="kg", product_id="123")

    assert item.name == "Apples"
    assert item.quantity == 5.0
    assert item.unit == "kg"
    assert item.product_id == "123"


@pytest.mark.unit
def test_basket_item_optional_fields():
    """Test BasketItem with optional fields."""
    item = BasketItem(name="Oranges", quantity=3.0)

    assert item.name == "Oranges"
    assert item.quantity == 3.0
    assert item.unit is None
    assert item.product_id is None


@pytest.mark.unit
def test_delivery_info_creation():
    """Test creating a DeliveryInfo."""
    delivery_date = datetime(2025, 11, 10, 12, 0)
    items = [
        BasketItem(name="Apples", quantity=5.0, unit="kg"),
        BasketItem(name="Oranges", quantity=3.0, unit="kg"),
    ]

    delivery_info = DeliveryInfo(delivery_date=delivery_date, items=items)

    assert delivery_info.delivery_date == delivery_date
    assert len(delivery_info.items) == 2
    assert delivery_info.total_items == 2


@pytest.mark.unit
def test_delivery_info_auto_total_items():
    """Test DeliveryInfo automatically calculates total_items."""
    items = [
        BasketItem(name="Item1", quantity=1.0),
        BasketItem(name="Item2", quantity=2.0),
        BasketItem(name="Item3", quantity=3.0),
    ]

    delivery_info = DeliveryInfo(delivery_date=None, items=items)

    assert delivery_info.total_items == 3


@pytest.mark.unit
def test_delivery_info_empty_items():
    """Test DeliveryInfo with empty items list."""
    delivery_info = DeliveryInfo(delivery_date=None, items=[])

    assert delivery_info.total_items == 0
    assert len(delivery_info.items) == 0
