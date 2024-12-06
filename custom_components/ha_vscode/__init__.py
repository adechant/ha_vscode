"""Provide the initial setup."""
import logging

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Provide Setup of platform."""
    return True


async def async_setup_entry(hass, config_entry):
    # Add sensor
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True
