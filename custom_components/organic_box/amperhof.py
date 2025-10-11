import aiohttp
from typing import Dict, Any
from .provider import OrganicBoxProvider
from .models import Item, Price, Basket, Delivery

class AmperhofProvider(OrganicBoxProvider):
    API_URL = "https://www.amperhof.de/api/basket/load"
    LOGIN_URL = "https://www.amperhof.de/proxy/user/login"

    _jwt_token = None
    _jwt_expiry = None

    @property
    def name(self) -> str:
        return "Amperhof"

    async def async_get_jwt_token(self):
        import time
        # Use cached token if valid
        if self._jwt_token and self._jwt_expiry and self._jwt_expiry > time.time():
            return self._jwt_token
        async with aiohttp.ClientSession() as session:
            async with session.post(self.LOGIN_URL, data={
                "username": self.config["username"],
                "password": self.config["password"]
            }) as resp:
                # Get JWT from Set-Cookie header
                cookies = resp.headers.get("Set-Cookie", "")
                import re
                match = re.search(r"JWT=([^;]+)", cookies)
                if not match:
                    raise Exception("Login failed: JWT not found in cookies")
                jwt_token = match.group(1)
                # Get expiry
                expiry_match = re.search(r"Expires=([^;]+)", cookies)
                import email.utils
                expiry = None
                if expiry_match:
                    expiry_str = expiry_match.group(1)
                    expiry = email.utils.parsedate_to_datetime(expiry_str).timestamp()
                else:
                    expiry = time.time() + 3600  # fallback: 1 hour
                self._jwt_token = jwt_token
                self._jwt_expiry = expiry
                return jwt_token

    async def async_get_next_delivery(self) -> Delivery:
        jwt_token = await self.async_get_jwt_token()
        headers = {
            "Cookie": f"JWT={jwt_token}"
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
