import pytest
from custom_components.organic_box.amperhof import AmperhofProvider

@pytest.mark.asyncio
async def test_amperhof_provider(monkeypatch):
    class DummyResponse:
        async def json(self):
            return {
                "data": {
                    "orderedBasket": [
                        {
                            "id": "1",
                            "amount": 1,
                            "price": 2.5,
                            "unit": {"unit": "kg"},
                            "information": {"name": "Apple", "category": "Fruit", "imageUrl": None},
                        }
                    ],
                    "order": {"billingSum": 2.5, "lastPossibleOrderChange": "2025-10-16", "address": "Test"}
                }
            }
    class DummySession:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
        async def get(self, url, headers): return DummyResponse()
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession())
    provider = AmperhofProvider({"jwt_token": "dummy"})
    delivery = await provider.async_get_next_delivery()
    assert delivery.date == "2025-10-16"
    assert delivery.basket.total_price.amount == 2.5
    assert delivery.basket.items[0].name == "Apple"
