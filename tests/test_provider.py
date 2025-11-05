"""Tests for organic_box provider."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.organic_box.models import DeliveryInfo
from custom_components.organic_box.provider import OrganicBoxProvider


class MockProvider(OrganicBoxProvider):
    """Mock implementation of OrganicBoxProvider for testing."""

    def __init__(self, hass: HomeAssistant, username: str, password: str) -> None:
        """Initialize mock provider."""
        super().__init__(hass, username, password)
        self.authenticate_called = False
        self.get_next_delivery_called = False
        self.test_connection_called = False
        self.close_called = False

    async def authenticate(self) -> bool:
        """Mock authenticate."""
        self.authenticate_called = True
        self._authenticated = True
        return True

    async def get_next_delivery(self) -> DeliveryInfo:
        """Mock get_next_delivery."""
        self.get_next_delivery_called = True
        return DeliveryInfo(delivery_date=None, items=[])

    async def test_connection(self) -> bool:
        """Mock test_connection."""
        self.test_connection_called = True
        return True

    @property
    def name(self) -> str:
        """Return provider name."""
        return "Mock Provider"

    async def close(self) -> None:
        """Mock close."""
        self.close_called = True


@pytest.mark.unit
async def test_provider_initialization(hass: HomeAssistant):
    """Test provider initialization."""
    provider = MockProvider(hass, "test_user", "test_pass")

    assert provider._username == "test_user"
    assert provider._password == "test_pass"
    assert provider._authenticated is False
    assert provider.is_authenticated is False


@pytest.mark.unit
async def test_provider_authenticate(hass: HomeAssistant):
    """Test provider authentication."""
    provider = MockProvider(hass, "test_user", "test_pass")

    result = await provider.authenticate()

    assert result is True
    assert provider.authenticate_called is True
    assert provider.is_authenticated is True


@pytest.mark.unit
async def test_provider_get_next_delivery(hass: HomeAssistant):
    """Test provider get_next_delivery."""
    provider = MockProvider(hass, "test_user", "test_pass")

    delivery_info = await provider.get_next_delivery()

    assert provider.get_next_delivery_called is True
    assert isinstance(delivery_info, DeliveryInfo)


@pytest.mark.unit
async def test_provider_test_connection(hass: HomeAssistant):
    """Test provider test_connection."""
    provider = MockProvider(hass, "test_user", "test_pass")

    result = await provider.test_connection()

    assert result is True
    assert provider.test_connection_called is True


@pytest.mark.unit
async def test_provider_name(hass: HomeAssistant):
    """Test provider name property."""
    provider = MockProvider(hass, "test_user", "test_pass")

    assert provider.name == "Mock Provider"


@pytest.mark.unit
async def test_provider_close(hass: HomeAssistant):
    """Test provider close."""
    provider = MockProvider(hass, "test_user", "test_pass")

    await provider.close()

    assert provider.close_called is True
