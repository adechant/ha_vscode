import re

from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import UnitOfInformation
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.typing import DiscoveryInfoType

from .vscode_device import VSCodeDeviceAPI


async def async_setup_entry(hass, config, async_add_devices):
    # Run setup via Storage
    dev_url = config.data["dev_url"]
    path = config.data["path"]
    async_add_devices([VSCodeEntity(path, dev_url)])


class VSCodeEntity(SwitchEntity):
    _attr_name = "Development URL"
    _attr_native_unit_of_measurement = UnitOfInformation
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, bin_dir, dev_url):
        self.device = VSCodeDeviceAPI(bin_dir)
        if dev_url.startswith("https://vscode.dev/tunnel/"):
            # try and output just the tunnel name
            slen = len("https://vscode.dev/tunnel/")
            dev_url = dev_url[slen:]
            match = re.search("^(.*)/", dev_url)
            if match:
                dev_url = match.group()[:-1]
        self._attr_name = "VSCode.dev Tunnel: " + dev_url

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self.device.startTunnel()

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self.device.stopTunnel()

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self.device.isRunning()
