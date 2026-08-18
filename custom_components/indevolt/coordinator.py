"""Home Assistant integration for indevolt device."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, Iterable

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN
from .opendata import IndevoltAPI
from .opendata.additional_points import (
    BK_ADDITIONAL_READ_GROUPS,
    DEFAULT_ADDITIONAL_READ_GROUPS,
    SIMULATED_LOAD_READ_POINTS,
)
from .opendata.polling import BK_POLLING_BASELINE, DEFAULT_POLLING_BASELINE

_LOGGER = logging.getLogger(__name__)
_SIMULATED_LOAD_READ_POINTS = frozenset(SIMULATED_LOAD_READ_POINTS)


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
            port=config.get("port", DEFAULT_PORT),
            session=async_get_clientsession(self.hass),
        )
        self._discover_optional_read_points = True
        self._enabled_optional_read_points: set[int] = set()

    def register_optional_read_point(self, point: int) -> None:
        """Keep polling one optional readback while its entity is enabled."""
        if point not in _SIMULATED_LOAD_READ_POINTS:
            return
        points = getattr(self, "_enabled_optional_read_points", None)
        if points is None:
            points = self._enabled_optional_read_points = set()
        points.add(point)

    def unregister_optional_read_point(self, point: int) -> None:
        """Stop polling one optional readback after its entity is removed."""
        points = getattr(self, "_enabled_optional_read_points", None)
        if points is not None:
            points.discard(point)

    def _active_additional_groups(
        self,
        groups: tuple[tuple[int, ...], ...],
    ) -> tuple[tuple[int, ...], ...]:
        """Discover disabled load slots once, then retain only enabled slots."""
        if getattr(self, "_discover_optional_read_points", True):
            return groups
        enabled = getattr(self, "_enabled_optional_read_points", set())
        return tuple(
            tuple(
                point
                for point in group
                if point not in _SIMULATED_LOAD_READ_POINTS or point in enabled
            )
            for group in groups
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch latest data from device."""
        try:
            if "BK1600" in self.config["device_model"]:
                polling_baseline = BK_POLLING_BASELINE
                additional_groups = BK_ADDITIONAL_READ_GROUPS
            else:
                polling_baseline = DEFAULT_POLLING_BASELINE
                additional_groups = self._active_additional_groups(
                    DEFAULT_ADDITIONAL_READ_GROUPS
                )

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
            finally:
                if "BK1600" not in self.config["device_model"]:
                    self._discover_optional_read_points = False

            _LOGGER.debug("Coordinator update finished (%d keys)", len(data))

            return data

        except Exception as err:
            _LOGGER.exception("Unexpected update error")
            raise UpdateFailed(f"Update failed: {err}") from err


def _chunked(iterable: list[int], size: int) -> Iterable[list[int]]:
    """Split list into chunks."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]
