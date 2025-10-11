"""Amperhof provider implementation for Organic Box integration."""

import email.utils
import re
import time
from collections import defaultdict

import aiohttp

from .models import Basket, Delivery, Item, Price
from .provider import OrganicBoxProvider


class AmperhofProvider(OrganicBoxProvider):
    """Provider for Amperhof organic box deliveries."""

    API_URL = "https://www.amperhof.de/api/basket/load"
    LOGIN_URL = "https://www.amperhof.de/proxy/user/login"

    _jwt_token = None
    _jwt_expiry = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "Amperhof"

    async def async_get_jwt_token(self) -> str:
        """Get JWT token for authentication."""
        # Use cached token if valid
        if self._jwt_token and self._jwt_expiry and self._jwt_expiry > time.time():
            return self._jwt_token
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.LOGIN_URL,
                data={
                    "username": self.config["username"],
                    "password": self.config["password"],
                },
            ) as resp:
                # Get JWT from Set-Cookie header
                cookies = resp.headers.get("Set-Cookie", "")
                match = re.search(r"JWT=([^;]+)", cookies)
                if not match:
                    raise Exception("Login failed: JWT not found in cookies")
                jwt_token = match.group(1)
                # Get expiry
                expiry_match = re.search(r"Expires=([^;]+)", cookies)
                expiry = None
                if expiry_match:
                    expiry_str = expiry_match.group(1)
                    expiry = email.utils.parsedate_to_datetime(expiry_str).timestamp()
                else:
                    expiry = time.time() + 3600  # fallback: 1 hour
                self._jwt_token = jwt_token
                self._jwt_expiry = expiry
                return jwt_token

    async def async_get_upcoming_deliveries(self) -> list:
        """Get upcoming deliveries from Amperhof API."""
        jwt_token = await self.async_get_jwt_token()
        headers = {
            "Cookie": f"JWT={jwt_token}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.API_URL, headers=headers) as resp:
                data = await resp.json()
        deliveries = []
        # Group items by deliveryDate
        items_by_date = defaultdict(list)
        for entry in data["data"]["orderedBasket"]:
            info = entry["information"]
            item = Item(
                id=entry["id"],
                name=info["name"],
                amount=entry["amount"],
                unit=entry["unit"]["unit"],
                price=Price(amount=entry["price"]),
                category=info["category"],
                image_url=info.get("imageUrl"),
            )
            delivery_date = entry.get("deliveryDate")
            if delivery_date:
                items_by_date[delivery_date].append(item)
        # For each delivery date, create a Delivery object
        for delivery_date, items in sorted(items_by_date.items()):
            total_price = sum(item.price.amount for item in items)
            basket = Basket(items=items, total_price=Price(amount=total_price))
            delivery = Delivery(
                date=delivery_date,
                basket=basket,
                address=data["data"]["order"].get("address"),
            )
            deliveries.append(delivery)
        return deliveries
