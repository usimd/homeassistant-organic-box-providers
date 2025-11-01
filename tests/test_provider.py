"""Tests for the abstract provider base class."""

import sys
from pathlib import Path
import pytest

# Add the component directory to the path
component_path = Path(__file__).parent.parent / "custom_components" / "organic_box"
sys.path.insert(0, str(component_path))

import models
import provider

BasketItem = models.BasketItem
DeliveryInfo = models.DeliveryInfo
OrganicBoxProvider = provider.OrganicBoxProvider


class MockProvider(OrganicBoxProvider):
    """Mock provider for testing."""

    @property
    def name(self) -> str:
        """Return the name of the provider."""
        return "Mock Provider"

    async def authenticate(self) -> bool:
        """Mock authenticate method."""
        self._authenticated = True
        return True

    async def get_next_delivery(self) -> DeliveryInfo:
        """Mock get_next_delivery method."""
        items = [BasketItem(name="Test Item", quantity=1)]
        return DeliveryInfo(delivery_date=None, items=items)

    async def test_connection(self) -> bool:
        """Mock test_connection method."""
        return True

    async def close(self) -> None:
        """Mock close method."""
        self._authenticated = False


def test_provider_initialization():
    """Test provider initialization."""
    provider = MockProvider("test_user", "test_pass")

    assert provider._username == "test_user"
    assert provider._password == "test_pass"
    assert not provider.is_authenticated


@pytest.mark.asyncio
async def test_provider_authenticate():
    """Test provider authentication."""
    provider = MockProvider("test_user", "test_pass")

    result = await provider.authenticate()

    assert result is True
    assert provider.is_authenticated


@pytest.mark.asyncio
async def test_provider_get_next_delivery():
    """Test getting next delivery."""
    provider = MockProvider("test_user", "test_pass")

    delivery = await provider.get_next_delivery()

    assert delivery is not None
    assert len(delivery.items) == 1
    assert delivery.items[0].name == "Test Item"


@pytest.mark.asyncio
async def test_provider_close():
    """Test closing provider connection."""
    provider = MockProvider("test_user", "test_pass")
    await provider.authenticate()

    assert provider.is_authenticated

    await provider.close()

    assert not provider.is_authenticated
