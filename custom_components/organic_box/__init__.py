"""The Organic Box integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_PROVIDER, CONF_SHOP_ID, DOMAIN, PROVIDER_OEKOBOX
from .coordinator import OrganicBoxDataUpdateCoordinator
from .oekobox import OekoBoxProvider
from .provider import OrganicBoxProvider

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Organic Box from a config entry."""
    provider_type = entry.data[CONF_PROVIDER]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    shop_id = entry.data.get(CONF_SHOP_ID)

    # Create the appropriate provider
    provider: OrganicBoxProvider
    if provider_type == PROVIDER_OEKOBOX:
        provider = OekoBoxProvider(hass, username, password, shop_id)
    else:
        _LOGGER.error("Unknown provider type: %s", provider_type)
        return False

    # Authenticate with the provider
    try:
        if not await provider.authenticate():
            raise ConfigEntryNotReady("Failed to authenticate with provider")
    except Exception as err:
        _LOGGER.error("Error authenticating with provider: %s", err)
        raise ConfigEntryNotReady from err

    # Create the data update coordinator
    coordinator = OrganicBoxDataUpdateCoordinator(hass, provider, entry)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up options flow listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close the provider connection
        coordinator: OrganicBoxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.provider.close()

        # Remove the coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
