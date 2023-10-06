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
import time
from .const import *

LOGGER: logging.Logger = logging.getLogger(PACKAGE_NAME)


class HAVSCodeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for ha_vscode."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self.device = None
        self.oauthcode = None
        self.devURL = None
        self._user_input = {}
        self._reauth = False
        self.log = LOGGER
        self.path = None

    async def async_step_user(self, user_input):
        if self.path is None:
            self.path = os.path.join(self.hass.config.path("custom_components"), DOMAIN)
            self.path = os.path.join(self.path, "bin")
            self.log.info("bin directory located at: " + self.path)

        """Handle a flow initialized by the user."""
        self._errors = {}
        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if [x for x in user_input if x.startswith("acc_") and not user_input[x]]:
                self._errors["base"] = "acc"
                return await self._show_config_form(user_input)

            self._user_input = user_input

            return await self.async_step_oauth(user_input)

        return await self._show_config_form(user_input)

    async def wait_for_activation(self, _user_input):
        result = self.device.activate(timeout=5)
        if not result:
            self._errors = HAVSCodeAuthenticationException()
        else:
            self.devURL = result

    async def wait_for_oauth(self, _user_input):
        self.device = VSCodeDeviceAPI(self.path)
        response = self.device.register(
            timeout=5
        )  # can specify a timeout here. default is 3 seconds
        if not response:
            self._errors = HAVSCodeAuthenticationException()
        self.oauthcode = response
        self.log.debug("set self.oauthcode")

    async def _async_do_task(self, task):
        await task  # A task that take some time to complete.

        # Continue the flow after show progress when the task is done.
        # To avoid a potential deadlock we create a new task that continues the flow.
        # The task must be completely done so the flow can await the task
        # if needed and get the task result.
        self.log.debug("Flow task start")
        await self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
        self.log.debug("Flow task end")

    def reason_for_error(self):
        # no switch in python until 3.10
        try:
            raise self._errors
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

    async def async_step_oauth(self, _user_input):
        self.log.debug("Entered async_step_oauth")
        if not self.oauthcode and not self._errors:
            self.hass.async_create_task(
                self._async_do_task(self.wait_for_oauth(_user_input))
            )
            progress_action = "wait_for_oauth"
            return self.async_show_progress(
                step_id="oauth",
                progress_action=progress_action,
            )

        if self._errors:
            self.log.debug(self._errors)
            return self.async_show_progress_done(next_step_id="last")

        self.log.debug("calling async_show_progress_done(next_step_id=activate)")
        return self.async_show_progress_done(next_step_id="activate")

    async def async_step_activate(self, _user_input):
        if not self.devURL and not self._errors:
            self.hass.async_create_task(
                self._async_do_task(self.wait_for_activation(_user_input))
            )
            progress_action = "wait_for_activation"
            placeholders = {
                "url": "https://github.com/login/device",
                "code": self.oauthcode,
            }
            return self.async_show_progress(
                step_id="activate",
                progress_action=progress_action,
                description_placeholders=placeholders,
            )

        if self._errors:
            self.log.debug(self._errors)
            self.log.debug(
                "calling async_show_progress_done(next_step_id=last) from async_step_activate"
            )
            return self.async_show_progress_done(next_step_id="last")

        self.log.debug("calling async_show_progress_done(next_step_id=finish)")
        return self.async_show_progress_done(next_step_id="finish")

    async def async_step_last(self, _user_input):
        reason = self.reason_for_error()
        self.log.debug("Reason for error to async_abort: " + reason)
        return self.async_abort(reason=reason)

    @callback
    async def async_remove(self):
        """Clean up resources or tasks associated with the flow."""
        self.log.info("Cleaning up...")
        if self.device:
            await self.device.stopTunnel()

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""

        if not user_input:
            user_input = {}

        if AwesomeVersion(HAVERSION) < MINIMUM_HA_VERSION:
            return self.async_abort(
                reason="min_ha_version",
                description_placeholders={"version": MINIMUM_HA_VERSION},
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "acc_git", default=user_input.get("acc_git", True)
                    ): bool,
                }
            ),
            errors=self._errors,
        )
