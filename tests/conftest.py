"""Fixtures for organic_box integration tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.organic_box.const import (
    CONF_PROVIDER,
    CONF_SHOP_ID,
    DOMAIN,
    PROVIDER_OEKOBOX,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture(name="mock_config_entry")
def mock_config_entry_fixture() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Organic Box",
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test_password",
            CONF_PROVIDER: PROVIDER_OEKOBOX,
            CONF_SHOP_ID: "test_shop_id",
        },
        unique_id="test@example.com",
    )


@pytest.fixture(name="mock_oekobox_client")
def mock_oekobox_client_fixture():
    """Return a mocked OekoboxClient."""
    mock_client = MagicMock()
    mock_client.logon = AsyncMock()
    mock_client.get_dates = AsyncMock(return_value=[])
    mock_client.get_orders = AsyncMock(return_value=[])
    mock_client.get_order_items = AsyncMock(return_value=[])
    mock_client.get_item = AsyncMock()
    mock_client.close = AsyncMock()
    return mock_client


@pytest.fixture(name="mock_oekobox_online")
def mock_oekobox_online_fixture(mock_oekobox_client):
    """Patch OekoBoxOnline with mocked client."""
    with patch(
        "custom_components.organic_box.oekobox.OekoBoxOnline",
        return_value=mock_oekobox_client,
    ) as mock:
        yield mock
