"""Provide the initial setup."""
import logging

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Provide Setup of platform."""
    return True


async def async_setup_entry(hass, config_entry):
    # Add sensor
    for platform in PLATFORMS:
        hass.async_add_job(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )
    return True
