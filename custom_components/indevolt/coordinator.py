"""Home Assistant integration for indevolt device."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, Iterable

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .indevolt_api import IndevoltAPI

_LOGGER = logging.getLogger(__name__)

class IndevoltDeviceUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=config.get("scan_interval", DEFAULT_SCAN_INTERVAL)),
        )
        self.config = config
        self.session = async_get_clientsession(hass)
        
        # Initialize Indevolt API.
        self.api = IndevoltAPI(
            host=config['host'],
            port=config['port'],
            session=async_get_clientsession(self.hass)
        )
    
    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest data from device."""
        try:
            keys=[]

            if "BK1600" in self.config["device_model"]:
                keys=[1501, 1502, 1505, 1664, 1665, 2101, 2107, 2108, 6000, 6001, 6002, 6004, 6005, 6006, 6007, 6105, 7101, 7120, 21028]
            else:
                keys=[142, 606, 667, 680,1118,1109,1119,1120,1136,1137,1138,1139,1140,1141,1142,1143,1098,1099,1501, 1502, 1600, 1601, 1602, 1603, 1632, 1633, 1634, 1635, 1664, 1665, 1666, 1667, 2101, 2104, 2105, 2107, 2108, 2600, 2612, 2618, 6000, 6001, 6002, 6004, 6005, 6006, 6007, 6105, 7101, 7120, 7171, 9000, 9004, 9008, 9009, 9011, 9012, 9013, 9016, 9020, 9021, 9023, 9030, 9032, 9035, 9039, 9040, 9042, 9049, 9051, 9054, 9058, 9059, 9061, 9068, 9070, 9149, 9153, 9154, 9156, 9163, 9165, 9202, 9206, 9216, 9218, 9219, 9222, 11009, 11010, 11011, 11016, 11034, 19173, 19174, 19175, 19176, 19177]
            
            data: Dict[str, Any] = {}

            for batch in _chunked(keys, 8):
                result = await self.api.fetch_data(batch)
                data.update(result)

            _LOGGER.debug("Coordinator update finished (%d keys)", len(data))
    
            return data
         
        except Exception as err:
            _LOGGER.exception("Unexpected update error")
            raise UpdateFailed(f"Update failed: {err}") from err


def _chunked(iterable: list[int], size: int) -> Iterable[list[int]]:
    """Split list into chunks."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]
