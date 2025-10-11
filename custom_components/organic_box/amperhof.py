import aiohttp
from typing import Dict, Any
from .provider import OrganicBoxProvider
from .models import Item, Price, Basket, Delivery

class AmperhofProvider(OrganicBoxProvider):
    API_URL = "https://www.amperhof.de/api/basket/load"

    @property
    def name(self) -> str:
        return "Amperhof"

    async def async_get_next_delivery(self) -> Delivery:
        headers = {
            "Cookie": f"JWT={self.config['jwt_token']}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.API_URL, headers=headers) as resp:
                data = await resp.json()
        items = []
        for entry in data["data"]["orderedBasket"]:
            info = entry["information"]
            items.append(Item(
                id=entry["id"],
                name=info["name"],
                amount=entry["amount"],
                unit=entry["unit"]["unit"],
                price=Price(amount=entry["price"]),
                category=info["category"],
                image_url=info.get("imageUrl")
            ))
        basket = Basket(items=items, total_price=Price(amount=data["data"]["order"]["billingSum"]))
        delivery = Delivery(
            date=data["data"]["order"]["lastPossibleOrderChange"],
            basket=basket,
            address=data["data"]["order"].get("address")
        )
        return delivery
