"""Tests for organic_box provider and AmperhofProvider."""

import asyncio
import sys
import types

import pytest

from custom_components.organic_box.amperhof import AmperhofProvider
from custom_components.organic_box.provider import OrganicBoxProvider

# Setup Home Assistant mocks
homeassistant_mod = types.ModuleType("homeassistant")
homeassistant_core_mod = types.ModuleType("homeassistant.core")
homeassistant_core_mod.HomeAssistant = type("HomeAssistant", (), {})
homeassistant_helpers_mod = types.ModuleType("homeassistant.helpers")
homeassistant_helpers_mod.service = None
homeassistant_helpers_typing_mod = types.ModuleType("homeassistant.helpers.typing")
homeassistant_helpers_typing_mod.ConfigType = dict
event_mod = types.ModuleType("homeassistant.helpers.event")


def async_track_time_interval(*args: object, **kwargs: object) -> None:
    """Mock async_track_time_interval for Home Assistant tests."""
    pass


event_mod.async_track_time_interval = async_track_time_interval
sys.modules["homeassistant"] = homeassistant_mod
sys.modules["homeassistant.core"] = homeassistant_core_mod
sys.modules["homeassistant.helpers"] = homeassistant_helpers_mod
sys.modules["homeassistant.helpers.event"] = event_mod
sys.modules["homeassistant.helpers.typing"] = homeassistant_helpers_typing_mod


def test_provider_base_methods() -> None:
    """Test DummyProvider name and delivery methods."""

    class DummyProvider(OrganicBoxProvider):
        @property
        def name(self) -> str:
            """Provider name."""
            return "Dummy"

        async def async_get_next_delivery(self) -> None:
            """Return None for test."""
            return None

    p = DummyProvider({})
    assert p.name == "Dummy"


def test_provider_base() -> None:
    """Test NotImplementedError for base provider."""
    provider = OrganicBoxProvider({})
    with pytest.raises(NotImplementedError):
        asyncio.run(provider.async_get_next_delivery())


def test_amperhof_name() -> None:
    """Test AmperhofProvider name property."""
    provider = AmperhofProvider({"jwt_token": "dummy"})
    assert provider.name == "Amperhof"
