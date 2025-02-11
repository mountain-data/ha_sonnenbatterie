import traceback
from homeassistant import config_entries,core
from homeassistant.core import callback
# pylint: disable=unused-wildcard-import
from .const import * #
from .sonnenbatterie_base import sonnenbatterie
from homeassistant.helpers import config_validation as cv
# pylint: enable=unused-wildcard-import
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_IP_ADDRESS,
    CONF_SCAN_INTERVAL,
)


class SonnenbatterieFlowHandler(config_entries.ConfigFlow,domain=DOMAIN):
    def __init__(self):
        """Initialize."""
        self.data_schema = CONFIG_SCHEMA_A
    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if not user_input:
            return self._show_form()

        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        ipaddress=user_input[CONF_IP_ADDRESS]
        time_zone=user_input[CONF_TIME_ZONE]


        try:
            def _internal_setup(_username,_password,_ipaddress):
                return sonnenbatterie(_username,_password,_ipaddress)
            sonnenInst=await self.hass.async_add_executor_job(_internal_setup,username,password,ipaddress);
        except:
            e = traceback.format_exc()
            LOGGER.error("Unable to connect to sonnenbatterie: %s", e)
            return self._show_form({"base": "connection_error"})

        return self.async_create_entry(
            title=user_input[CONF_IP_ADDRESS],
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_IP_ADDRESS: ipaddress,
                CONF_TIME_ZONE: time_zone,
            },
        )

    @callback
    def _show_form(self, errors=None):
        """Show the form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=self.data_schema,
            errors=errors if errors else {},
        )

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)


    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): cv.positive_int,
                    vol.Optional(ATTR_SONNEN_DEBUG, default=self.config_entry.options.get(ATTR_SONNEN_DEBUG, DEFAULT_SONNEN_DEBUG)): bool,
                }
            )
        )
    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(title="", data=self.options)
