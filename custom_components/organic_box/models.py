"""Data models for the Organic Box integration."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BasketItem:
    """Representation of an item in the basket."""

    name: str
    quantity: float
    unit: str | None = None
    product_id: str | None = None


@dataclass
class DeliveryInfo:
    """Representation of delivery information."""

    delivery_date: datetime | None
    items: list[BasketItem]
    total_items: int = 0

    def __post_init__(self):
        """Calculate total items if not provided."""
        if self.total_items == 0:
            self.total_items = len(self.items)
