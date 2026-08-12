import asyncio
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import IndevoltAPI

_LOGGER = logging.getLogger(__name__)

class IndevoltConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration flow for Indevolt integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """
        Handle the initial user configuration step.
        This method is called when the user initiates the integration setup.
        It presents a form for device connection parameters and validates them.
        """
        
        errors = {}
        if user_input is not None:
            host = user_input["host"]
            scan_interval = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)

            api = IndevoltAPI(host, DEFAULT_PORT, async_get_clientsession(self.hass))            

            try:
                data = await api.get_config()

                device = data.get("device", {})
                device_model = device.get("type")
                device_sn = device.get("sn")

                if "SF2000" in device_model:
                    device_model = "SolidFlex/PowerFlex2000"
                elif "BK1600" in device_model:
                    device_model = "BK1600/BK1600Ultra"

                await self.async_set_unique_id(device_sn)
                self._abort_if_unique_id_configured()

                # Create configuration entry on successful connection.
                return self.async_create_entry(
                    title=f"INDEVOLT {device_model} ({host})", # Entry title shown in HA UI.
                    data={
                        "host": host,
                        "port": DEFAULT_PORT,
                        "scan_interval": scan_interval,
                        "sn": device_sn,
                        "device_model": device_model,
                        "fw_version": device.get("f_ver")
                    }
                )
            
            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except Exception as e:
                _LOGGER.error("Unknown error occurred while verifying device: %s", str(e), exc_info=True)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
            }),
            errors=errors
        )