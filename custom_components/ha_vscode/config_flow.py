"""Adds config flow for VSCode HA Tunnel."""
from awesomeversion import AwesomeVersion
from homeassistant import config_entries
from homeassistant.const import __version__ as HAVERSION
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.event import async_call_later
from homeassistant.loader import async_get_integration
import voluptuous as vol
from .vscode_device import VSCodeDeviceAPI
import logging
from .const import DOMAIN, MINIMUM_HA_VERSION, PACKAGE_NAME

LOGGER: logging.Logger = logging.getLogger(PACKAGE_NAME)


class HAVSCodeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for ha_vscode."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self.device = None
        self._login_device = None
        self.activation = None
        self._user_input = {}
        self._reauth = False
        self.log = LOGGER

    async def async_step_user(self, user_input):
        """Handle a flow initialized by the user."""
        self._errors = {}
        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input:
            if [x for x in user_input if x.startswith("acc_") and not user_input[x]]:
                self._errors["base"] = "acc"
                return await self._show_config_form(user_input)

            self._user_input = user_input

            await self.async_step_device(user_input)
            return self.async_abort(reason="done_debug")

        return await self._show_config_form(user_input)

    async def async_step_device(self, _user_input):
        """Handle device steps"""

        self.log.info(self.flow_id)

        async def _wait_for_activation(_=None):
            if self._login_device is None:
                async_call_later(self.hass, 1, _wait_for_activation)
                return
            response = await self.device.activation()
            self.log.info(response)
            self.activation = response
            self.log.info(self.flow_id)

        if not self.activation:
            integration = await async_get_integration(self.hass, DOMAIN)
            if not self.device:
                self.device = VSCodeDeviceAPI()
            async_call_later(self.hass, 1, _wait_for_activation)
            try:
                response = await self.device.register()
                self._login_device = response
                self.log.info(response)
                return self.async_show_progress(
                    step_id="device",
                    progress_action="wait_for_device",
                    description_placeholders={
                        "url": "PUT GITHUB URL HERE FROM ./code tunnel",
                        "code": "PUT GITHUB OATH TOKEN HERE FROM ./code tunnel",
                    },
                )
            except Exception as exception:
                self.log.error(exception)
                return self.async_abort(reason="github")

        return self.async_show_progress_done(next_step_id="device_done")

    async def async_step_device_done(self, user_input: dict[str, bool] | None = None):
        """Handle device steps"""

        if self._reauth:
            existing_entry = self.hass.config_entries.async_get_entry(
                self.context["entry_id"]
            )
            self.hass.config_entries.async_update_entry(
                existing_entry,
                data={**existing_entry.data, "token": self.activation.access_token},
            )
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(
            title="",
            data={
                "token": self.activation.access_token,
            },
            options={
                "experimental": self._user_input.get("experimental", False),
            },
        )

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
                        "acc_logs", default=user_input.get("acc_logs", True)
                    ): bool,
                    vol.Required(
                        "acc_git", default=user_input.get("acc_git", True)
                    ): bool,
                }
            ),
            errors=self._errors,
        )
