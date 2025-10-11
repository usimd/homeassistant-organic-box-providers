from custom_components.organic_box.models import Price, Item, Basket, Delivery

def test_price():
    p = Price(amount=5.0)
    assert p.amount == 5.0
    assert p.currency == "EUR"

def test_item():
    price = Price(amount=2.5)
    item = Item(id="1", name="Apple", amount=1, unit="kg", price=price, category="Fruit")
    assert item.name == "Apple"
    assert item.price.amount == 2.5

def test_basket():
    price = Price(amount=10.0)
    items = [Item(id="1", name="Apple", amount=1, unit="kg", price=price, category="Fruit")]
    basket = Basket(items=items, total_price=price)
    assert len(basket.items) == 1
    assert basket.total_price.amount == 10.0

def test_delivery():
    price = Price(amount=10.0)
    items = [Item(id="1", name="Apple", amount=1, unit="kg", price=price, category="Fruit")]
    basket = Basket(items=items, total_price=price)
    delivery = Delivery(date="2025-10-16", basket=basket)
    assert delivery.date == "2025-10-16"
    assert delivery.basket.total_price.amount == 10.0
