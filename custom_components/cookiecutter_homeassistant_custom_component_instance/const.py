"""Constants for Cookiecutter Home Assistant Custom Component Instance."""
# Base component constants
NAME = "Cookiecutter Home Assistant Custom Component Instance"
DOMAIN = "cookiecutter_homeassistant_custom_component_instance"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0"

ISSUE_URL = "https://github.com/oncleben31/cookiecutter-homeassistant-custom-component-instance/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
SWITCH = "switch"
PLATFORMS = [BINARY_SENSOR, SENSOR, SWITCH]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
