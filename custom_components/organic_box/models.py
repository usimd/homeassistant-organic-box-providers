"""Organic Box models for Home Assistant integration."""

from dataclasses import dataclass


@dataclass
class Price:
    """Represents a price with amount and currency."""

    amount: float
    currency: str = "EUR"


@dataclass
class Item:
    """Represents an item in a basket."""

    id: str
    name: str
    amount: float
    unit: str
    price: Price
    category: str
    image_url: str | None = None


@dataclass
class Basket:
    """Represents a basket containing items and total price."""

    items: list[Item]
    total_price: Price


@dataclass
class Delivery:
    """Represents a delivery with date and basket."""

    date: str
    basket: Basket
    address: str | None = None
