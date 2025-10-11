from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Price:
    amount: float
    currency: str = "EUR"

@dataclass
class Item:
    id: str
    name: str
    amount: float
    unit: str
    price: Price
    category: str
    image_url: Optional[str] = None

@dataclass
class Basket:
    items: List[Item]
    total_price: Price

@dataclass
class Delivery:
    date: str
    basket: Basket
    address: Optional[str] = None
