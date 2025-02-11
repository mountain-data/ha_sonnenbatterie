import logging
import voluptuous as vol
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_IP_ADDRESS,
    CONF_SCAN_INTERVAL,
    CONF_TIME_ZONE
)
LOGGER = logging.getLogger(__package__)

DOMAIN = "sonnenbatterie_bb"
DEFAULT_SCAN_INTERVAL = 10
DEFAULTTIME_ZONE = 'Europe/Berlin'

CONFIG_SCHEMA_A=vol.Schema(
            {
                vol.Required(CONF_USERNAME): vol.In(["User", "Installer"]),
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_IP_ADDRESS): str,
                vol.Required(CONF_TIME_ZONE): vol.In(['Europe/Berlin', 'Europe/Dublin']),
            }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: CONFIG_SCHEMA_A
    },
    extra=vol.ALLOW_EXTRA,
)

ATTR_SONNEN_DEBUG = "sonnenbatterie_debug"
DEFAULT_SONNEN_DEBUG = False
PLATFORMS = ["sensor"]

def flattenObj(prefix,seperator,obj):
    result={}
    for field in obj:
        val=obj[field]
        valprefix=prefix+seperator+field
        if type(val) is dict:
            sub=flattenObj(valprefix,seperator,val)
            result.update(sub)
        else:
            result[valprefix]=val
    return result
