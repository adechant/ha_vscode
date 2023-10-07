"""Adds config flow for VSCode HA Tunnel."""
from awesomeversion import AwesomeVersion
from homeassistant import config_entries
from homeassistant.const import __version__ as HAVERSION
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.event import async_call_later
from homeassistant.loader import async_get_integration
from homeassistant.helpers.storage import STORAGE_DIR
import voluptuous as vol
from .vscode_device import VSCodeDeviceAPI
from .exceptions import *
import logging
import os.path
from .const import *

LOGGER: logging.Logger = logging.getLogger(PACKAGE_NAME)


class HAVSCodeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for ha_vscode."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._error = None
        self.device = None
        self.oauthToken = None
        self.devURL = None
        self.log = LOGGER
        self.path = None
        self.activate = False

    async def async_step_user(self, user_input):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if AwesomeVersion(HAVERSION) < MINIMUM_HA_VERSION:
            return self.async_abort(
                reason="min_ha_version",
                description_placeholders={"version": MINIMUM_HA_VERSION},
            )

        if self.path is None:
            self.path = os.path.join(self.hass.config.path("custom_components"), DOMAIN)
            self.path = os.path.join(self.path, "bin")
            self.log.info("bin directory located at: " + self.path)

        if self.device is None:
            self.device = VSCodeDeviceAPI(self.path)
            response = await self.device.register(
                timeout=5
            )  # can specify a timeout here. default is 3 seconds
            if response is None:
                # check to see if we are somehow already authenticated
                response = self.device.getDevURL(timeout=5.0)
                if response is None:
                    self._error = HAVSCodeAuthenticationException()
                else:
                    self.devURL = response
            else:
                self.oauthToken = response

        if self._error is not None:
            return self.async_abort(reason=self.reason_for_error())
        if self.oauthToken is not None and self.activate:
            return await self.async_step_activate(user_input)
        elif self.devURL is not None:
            # set the auth token to "already_registered"
            self.oauthToken = "already_registered"
            return await self.async_step_activate(user_input)

        return await self._show_config_form(user_input)

    def reason_for_error(self):
        # no switch in python until 3.10
        try:
            raise self._error
        except HAVSCodeDownloadException:
            return "download"
        except HAVSCodeAuthenticationException:
            return "authentication"
        except HAVSCodeTarException:
            return "tar"
        except HAVSCodeZipException:
            return "zip"
        except Exception:
            return "unknown"

        return "unknown"

    async def async_step_activate(self, _user_input):
        if not self.devURL and not self._error:
            result = await self.device.activate(timeout=3)
            if not result:
                self._error = HAVSCodeAuthenticationException()
            else:
                self.devURL = result

        if self._error:
            reason = self.reason_for_error()
            self.log.debug("Reason activation error: " + reason)
            return self.async_abort(reason=reason)

        # create entry and finish.
        return self.async_create_entry(
            title="HA VSCode Tunnel",
            data={
                "token": self.oauthToken,
                "dev_url": self.devURL,
                "path": self.path,
                "timeout": 5.0,
            },
            description="Created configuration for HA VSCode Tunnel.\nPlease access VSCode instance at {url}",
            description_placeholders={
                "url": self.devURL,
            },
        )

    @callback
    def async_remove(self):
        """Clean up resources or tasks associated with the flow."""
        self.log.info("Cleaning up...")
        if self.device:
            self.device.stopTunnel()

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""

        self.activate = True

        return self.async_show_form(
            step_id="user",
            data_schema=None,
            description_placeholders={
                "url": "https://github.com/login/device",
                "token": self.oauthToken,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return HAVSCodeOptionsFlowHandler(config_entry)


class HAVSCodeOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.device = None
        self.path = config_entry.options.get("path")
        self.dev_url = config_entry.options.get("dev_url")
        self.timeout = config_entry.options.get("timeout")
        self.log = LOGGER
        self._reauth = False

    async def async_step_init(self, _user_input=None):
        if self.path is None:
            self.path = os.path.join(self.hass.config.path("custom_components"), DOMAIN)
            self.path = os.path.join(self.path, "bin")
            self.log.debug("bin directory located at: " + self.path)

        if self.device is None:
            # start a tunnel and see if an oauth token is generated. if it is, then we need to reauth.
            self.device = VSCodeDeviceAPI(self.path)
            self.device.startTunnel()
            token = await self.device.getOAuthToken()
            if token is not None:
                self.log.debug("Token received during config setup was: " + token)
                self._reauth = True
            url = await self.device.getDevURL()
            if self.dev_url is None:
                self.dev_url = url
            self.device.stopTunnel()

        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        havsc = self.hass.data.get(DOMAIN)
        if user_input is not None:
            _reauth = bool(user_input.get("needs_reauth", False))
            _timeout = float(user_input.get("timeout")), 5.0
            if self.timeout != _timeout:
                return self.async_create_entry(
                    title="HA VSCode Tunnel",
                    data={
                        "token": self.oauthToken,
                        "dev_url": self.devURL,
                        "path": self.path,
                    },
                    description="Created configuration for HA VSCode Tunnel.\nPlease access VSCode instance at {url}",
                    description_placeholders={
                        "url": self.devURL,
                    },
                )

            return self.async_abort(reason="no_reauth_needed")

        if self.config_entry is None:
            return self.async_abort(reason="not_setup")

        schema = {
            vol.Optional("needs_reauth", default=self._reauth): bool,
            vol.Optional("timeout", default=self.timeout): float,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            description_placeholders={
                "url": self.dev_url,
            },
        )
