"""Sensor platform for Cookiecutter Home Assistant Custom Component Instance."""
from .const import DEFAULT_NAME, DOMAIN, ICON, SENSOR
from .entity import CookiecutterHomeassistantCustomComponentInstanceEntity

from homeassistant.util import slugify


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([CookiecutterHomeassistantCustomComponentInstanceSensor(coordinator, entry)])


class CookiecutterHomeassistantCustomComponentInstanceSensor(CookiecutterHomeassistantCustomComponentInstanceEntity):
    """cookiecutter_homeassistant_custom_component_instance Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    @property
    def state(self):
        """Return the state of the sensor."""
        # slugify the state to allow translation
        return slugify(self.coordinator.data.get("static"))

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON
    
    @property
    def device_class(self):
        """Retrun device_class for sensor."""
        return "cookiecutter_homeassistant_custom_component_instance__custom_device_class"
