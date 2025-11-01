"""Config flow for Organic Box integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_PROVIDER, CONF_SHOP_ID, DOMAIN, PROVIDER_OEKOBOX
from .oekobox import OekoBoxProvider

_LOGGER = logging.getLogger(__name__)

PROVIDERS = {
    PROVIDER_OEKOBOX: "OekoBox Online",
}


class OrganicBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Organic Box."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._provider: str | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._shop_id: str | None = None
        self._available_shops: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - provider selection."""
        errors = {}

        if user_input is not None:
            self._provider = user_input[CONF_PROVIDER]
            return await self.async_step_credentials()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_PROVIDER): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": key, "label": value}
                            for key, value in PROVIDERS.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the credentials step."""
        errors = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]

            # For OekoBox, we need to get shop selection
            if self._provider == PROVIDER_OEKOBOX:
                try:
                    provider = OekoBoxProvider(self._username, self._password)
                    self._available_shops = await provider.get_available_shops()
                    await provider.close()

                    if not self._available_shops:
                        errors["base"] = "no_shops_found"
                    else:
                        # Proceed to shop selection
                        return await self.async_step_shop_selection()
                except Exception as err:
                    _LOGGER.error("Error fetching shops: %s", err)
                    errors["base"] = "cannot_connect"
            else:
                # For other providers, test credentials directly
                if await self._test_credentials():
                    await self.async_set_unique_id(f"{self._provider}_{self._username}")
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"{PROVIDERS[self._provider]} ({self._username})",
                        data={
                            CONF_PROVIDER: self._provider,
                            CONF_USERNAME: self._username,
                            CONF_PASSWORD: self._password,
                        },
                    )
                else:
                    errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="credentials",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "provider": PROVIDERS.get(self._provider, "Unknown")
            },
        )

    async def async_step_shop_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the shop selection step for OekoBox."""
        errors = {}

        if user_input is not None:
            self._shop_id = user_input[CONF_SHOP_ID]

            # Test the credentials with the selected shop
            if await self._test_credentials():
                # Create a unique ID based on provider, username, and shop
                await self.async_set_unique_id(
                    f"{self._provider}_{self._username}_{self._shop_id}"
                )
                self._abort_if_unique_id_configured()

                # Get the shop name for the title
                shop_name = self._available_shops.get(self._shop_id, self._shop_id)

                return self.async_create_entry(
                    title=f"{PROVIDERS[self._provider]} - {shop_name} ({self._username})",
                    data={
                        CONF_PROVIDER: self._provider,
                        CONF_USERNAME: self._username,
                        CONF_PASSWORD: self._password,
                        CONF_SHOP_ID: self._shop_id,
                    },
                )
            else:
                errors["base"] = "cannot_connect"

        # Create options for the dropdown
        shop_options = [
            {"value": shop_id, "label": shop_name}
            for shop_id, shop_name in self._available_shops.items()
        ]

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SHOP_ID): SelectSelector(
                    SelectSelectorConfig(
                        options=shop_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="shop_selection",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "provider": PROVIDERS.get(self._provider, "Unknown"),
                "username": self._username,
            },
        )

    async def _test_credentials(self) -> bool:
        """Test if the credentials are valid."""
        try:
            if self._provider == PROVIDER_OEKOBOX:
                provider = OekoBoxProvider(
                    self._username, self._password, self._shop_id
                )
                result = await provider.test_connection()
                await provider.close()
                return result
            else:
                _LOGGER.error("Unknown provider: %s", self._provider)
                return False
        except Exception as err:
            _LOGGER.error("Error testing credentials: %s", err)
            return False
