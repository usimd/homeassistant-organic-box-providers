"""Tests for the Organic Box models."""

from datetime import datetime
from custom_components.organic_box.models import BasketItem, DeliveryInfo


def test_basket_item_creation():
    """Test creating a basket item."""
    item = BasketItem(
        name="Apples",
        quantity=5,
        unit="kg",
        product_id="123",
    )

    assert item.name == "Apples"
    assert item.quantity == 5
    assert item.unit == "kg"
    assert item.product_id == "123"


def test_basket_item_without_optional_fields():
    """Test creating a basket item without optional fields."""
    item = BasketItem(
        name="Bananas",
        quantity=3,
    )

    assert item.name == "Bananas"
    assert item.quantity == 3
    assert item.unit is None
    assert item.product_id is None


def test_delivery_info_creation():
    """Test creating delivery info."""
    delivery_date = datetime(2025, 11, 15, 10, 0, 0)
    items = [
        BasketItem(name="Apples", quantity=5, unit="kg"),
        BasketItem(name="Bananas", quantity=3, unit="kg"),
    ]

    delivery = DeliveryInfo(
        delivery_date=delivery_date,
        items=items,
    )

    assert delivery.delivery_date == delivery_date
    assert len(delivery.items) == 2
    assert delivery.total_items == 2


def test_delivery_info_auto_count():
    """Test that total_items is automatically calculated."""
    items = [
        BasketItem(name="Item1", quantity=1),
        BasketItem(name="Item2", quantity=1),
        BasketItem(name="Item3", quantity=1),
    ]

    delivery = DeliveryInfo(
        delivery_date=None,
        items=items,
    )

    assert delivery.total_items == 3
