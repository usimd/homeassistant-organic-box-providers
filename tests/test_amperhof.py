import asyncio
import sys
import types

import pytest

from custom_components.organic_box import amperhof
from custom_components.organic_box.amperhof import AmperhofProvider

"""Tests for AmperhofProvider and Home Assistant mocks."""

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
    """Mock async_track_time_interval."""
    pass


event_mod.async_track_time_interval = async_track_time_interval
sys.modules["homeassistant"] = homeassistant_mod
sys.modules["homeassistant.core"] = homeassistant_core_mod
sys.modules["homeassistant.helpers"] = homeassistant_helpers_mod
sys.modules["homeassistant.helpers.event"] = event_mod
sys.modules["homeassistant.helpers.typing"] = homeassistant_helpers_typing_mod


def test_amperhof_provider_init() -> None:
    """Test AmperhofProvider config initialization."""
    provider = amperhof.AmperhofProvider(
        {
            "username": "user",
            "password": "testpass",
        }
    )
    assert provider.config["username"] == "user"
    assert provider.config["password"] == "testpass"


def test_amperhof_provider_not_implemented() -> None:
    """Test NotImplementedError for async_get_next_delivery."""
    provider = AmperhofProvider({"jwt_token": "dummy"})
    with pytest.raises(NotImplementedError):
        asyncio.run(provider.async_get_next_delivery())
    with pytest.raises(NotImplementedError):
        asyncio.run(provider.async_get_next_delivery())
