"""SolidFlex2000 polling-point contract."""

from __future__ import annotations

import pytest

from custom_components.indevolt.coordinator import IndevoltDeviceUpdateCoordinator
from tests.models._opendata_point_additions import (
    BASELINE_DEFAULT_POINT_BATCHES,
    DEFAULT_CAPABILITY_POINT_BATCHES,
    DEFAULT_CAPABILITY_READ_POINTS,
    flattened,
)

MODEL = "SolidFlex/PowerFlex2000"


class RecordingAPI:
    def __init__(self) -> None:
        self.batches = []

    async def fetch_data(self, batch):
        self.batches.append(list(batch))
        return {str(point): point for point in batch}


@pytest.mark.asyncio
async def test_solidflex2000_polls_its_own_point_contract() -> None:
    api = RecordingAPI()
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": MODEL}
    coordinator.api = api

    data = await coordinator._async_update_data()

    expected_batches = BASELINE_DEFAULT_POINT_BATCHES + DEFAULT_CAPABILITY_POINT_BATCHES
    points = tuple(point for batch in api.batches for point in batch)
    assert api.batches == [list(batch) for batch in expected_batches]
    assert points == flattened(expected_batches)
    assert 21028 not in points
    assert set(data) == {str(point) for point in points}


@pytest.mark.parametrize(
    "point",
    DEFAULT_CAPABILITY_READ_POINTS,
    ids=lambda point: f"point_{point}",
)
@pytest.mark.asyncio
async def test_solidflex2000_polls_each_additional_read_point(point: int) -> None:
    """Every documented user-capability value reaches the coordinator snapshot."""
    api = RecordingAPI()
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": MODEL}
    coordinator.api = api

    data = await coordinator._async_update_data()

    assert point in {requested for batch in api.batches for requested in batch}
    assert data[str(point)] == point
