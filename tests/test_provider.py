import pytest
from custom_components.organic_box.provider import OrganicBoxProvider
from custom_components.organic_box.amperhof import AmperhofProvider

class DummyProvider(OrganicBoxProvider):
    @property
    def name(self):
        return "Dummy"
    async def async_get_next_delivery(self):
        return None

def test_provider_base():
    provider = DummyProvider({})
    assert provider.name == "Dummy"
    with pytest.raises(NotImplementedError):
        _ = OrganicBoxProvider({}).async_get_next_delivery()

def test_amperhof_name():
    provider = AmperhofProvider({"jwt_token": "dummy"})
    assert provider.name == "Amperhof"
