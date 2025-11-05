"""Test the organic_box config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.organic_box.const import (
    CONF_PROVIDER,
    CONF_SHOP_ID,
    DOMAIN,
    PROVIDER_OEKOBOX,
)


@pytest.mark.integration
async def test_user_flow_show_form(hass: HomeAssistant) -> None:
    """Test initial form is shown for user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert CONF_PROVIDER in result["data_schema"].schema


@pytest.mark.integration
async def test_user_flow_credentials_step(hass: HomeAssistant) -> None:
    """Test credentials step is shown after provider selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select provider
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PROVIDER: PROVIDER_OEKOBOX},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "credentials"


@pytest.mark.integration
async def test_user_flow_shop_selection(hass: HomeAssistant) -> None:
    """Test shop selection step for OekoBox provider."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select provider
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PROVIDER: PROVIDER_OEKOBOX},
    )

    # Mock get_shop_info
    mock_shop = MagicMock()
    mock_shop.id = "test_shop_123"
    mock_shop.name = "Test Shop"

    with patch(
        "custom_components.organic_box.config_flow.OekoboxClient.get_shop_info",
        return_value=[mock_shop],
    ):
        # Enter credentials
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "username": "test@example.com",
                "password": "test_password",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "shop_selection"
    assert CONF_SHOP_ID in result["data_schema"].schema


@pytest.mark.integration
async def test_user_flow_complete(hass: HomeAssistant) -> None:
    """Test complete config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select provider
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PROVIDER: PROVIDER_OEKOBOX},
    )

    # Mock get_shop_info
    mock_shop = MagicMock()
    mock_shop.id = "test_shop_123"
    mock_shop.name = "Test Shop"

    with patch(
        "custom_components.organic_box.config_flow.OekoboxClient.get_shop_info",
        return_value=[mock_shop],
    ):
        # Enter credentials
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "username": "test@example.com",
                "password": "test_password",
            },
        )

    # Mock OekoBoxOnline client
    with patch(
        "custom_components.organic_box.oekobox.OekoBoxOnline"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.logon = AsyncMock()
        mock_client.get_dates = AsyncMock(return_value=[])
        mock_client.get_orders = AsyncMock(return_value=[])
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        # Select shop
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_SHOP_ID: "test_shop_123"},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "OekoBox Online - Test Shop (test@example.com)"
    assert result["data"][CONF_PROVIDER] == PROVIDER_OEKOBOX
    assert result["data"]["username"] == "test@example.com"
    assert result["data"][CONF_SHOP_ID] == "test_shop_123"


@pytest.mark.integration
async def test_user_flow_no_shops_error(hass: HomeAssistant) -> None:
    """Test error when no shops are found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select provider
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PROVIDER: PROVIDER_OEKOBOX},
    )

    # Mock get_shop_info returning empty list
    with patch(
        "custom_components.organic_box.config_flow.OekoboxClient.get_shop_info",
        return_value=[],
    ):
        # Enter credentials
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "username": "test@example.com",
                "password": "test_password",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "no_shops_found"


@pytest.mark.integration
async def test_user_flow_connection_error(hass: HomeAssistant) -> None:
    """Test error handling for connection failures."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select provider
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PROVIDER: PROVIDER_OEKOBOX},
    )

    # Mock get_shop_info raising exception
    with patch(
        "custom_components.organic_box.config_flow.OekoboxClient.get_shop_info",
        side_effect=Exception("Connection error"),
    ):
        # Enter credentials
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "username": "test@example.com",
                "password": "test_password",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"
