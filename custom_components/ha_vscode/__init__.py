"""
Custom integration to integrate VSCode Home Assistant Tunnel with Home Assistant.

For more details about this integration, please refer to
https://github.com/adechant/ha_vscode
"""
import logging

from homeassistant.core import Config
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .const import PLATFORMS

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config):
    return True


async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI/YAML."""
    # config_entry.data = ensure_config(config_entry.data)  # make sure that missing storage values will be default (const function)
    config_entry.options = config_entry.data
    config_entry.add_update_listener(update_listener)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {}

    # Add sensor
    for platform in PLATFORMS:
        hass.async_add_job(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )
    return True


async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    for platform in PLATFORMS:
        try:
            await hass.config_entries.async_forward_entry_unload(config_entry, platform)
            _LOGGER.info("Successfully removed sensor from the integration")
        except ValueError:
            pass


async def update_listener(hass, entry):
    """Update listener."""
    entry.data = entry.options
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, platform)
        hass.async_add_job(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
