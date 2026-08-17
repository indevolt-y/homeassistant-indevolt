"""Home Assistant integration for indevolt device."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, Iterable

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .opendata import IndevoltAPI
from .opendata.additional_points import (
    BK_ADDITIONAL_READ_GROUPS,
    DEFAULT_ADDITIONAL_READ_GROUPS,
)
from .opendata.polling import BK_POLLING_BASELINE, DEFAULT_POLLING_BASELINE

_LOGGER = logging.getLogger(__name__)


class IndevoltDeviceUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=config.get("scan_interval", DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.config = config
        self.session = async_get_clientsession(hass)

        # Initialize Indevolt API.
        self.api = IndevoltAPI(
            host=config["host"],
            port=config["port"],
            session=async_get_clientsession(self.hass),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest data from device."""
        try:
            if "BK1600" in self.config["device_model"]:
                polling_baseline = BK_POLLING_BASELINE
                additional_groups = BK_ADDITIONAL_READ_GROUPS
            else:
                polling_baseline = DEFAULT_POLLING_BASELINE
                additional_groups = DEFAULT_ADDITIONAL_READ_GROUPS

            data: Dict[str, Any] = {}

            baseline_points = [field.point for field in polling_baseline]
            for batch in _chunked(baseline_points, 8):
                result = await self.api.fetch_data(batch)
                data.update(result)

            additional_data: Dict[str, Any] = {}
            try:
                for point_group in additional_groups:
                    for batch in _chunked(list(point_group), 8):
                        result = await self.api.fetch_data(batch)
                        additional_data.update(result)
            except Exception as err:
                _LOGGER.debug(
                    "Additional OpenData points are unavailable; keeping the "
                    "baseline update: %s",
                    err,
                )
            else:
                data.update(additional_data)

            _LOGGER.debug("Coordinator update finished (%d keys)", len(data))

            return data

        except Exception as err:
            _LOGGER.exception("Unexpected update error")
            raise UpdateFailed(f"Update failed: {err}") from err


def _chunked(iterable: list[int], size: int) -> Iterable[list[int]]:
    """Split list into chunks."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]
