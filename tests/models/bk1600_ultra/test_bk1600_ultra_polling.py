"""BK1600Ultra polling-point contract."""

from __future__ import annotations

import pytest

from custom_components.indevolt.coordinator import IndevoltDeviceUpdateCoordinator
from tests.models._opendata_point_additions import (
    ADDITIONAL_DEFAULT_READ_POINTS,
    REMAINING_BK_READ_POINTS,
)

MODEL = "BK1600/BK1600Ultra"


class RecordingAPI:
    def __init__(self) -> None:
        self.batches = []

    async def fetch_data(self, batch):
        self.batches.append(list(batch))
        return {str(point): point for point in batch}


@pytest.mark.asyncio
async def test_bk1600_ultra_polls_its_own_point_contract() -> None:
    api = RecordingAPI()
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": MODEL}
    coordinator.api = api

    data = await coordinator._async_update_data()

    points = {point for batch in api.batches for point in batch}
    assert [len(batch) for batch in api.batches] == [8, 8, 3]
    assert len(points) == 19
    assert {1501, 1505, 6001, 21028} <= points
    assert points.isdisjoint({142, 19177})
    assert points.isdisjoint(ADDITIONAL_DEFAULT_READ_POINTS)
    assert set(data) == {str(point) for point in points}


@pytest.mark.parametrize(
    "point",
    REMAINING_BK_READ_POINTS,
    ids=lambda point: f"point_{point}",
)
@pytest.mark.asyncio
async def test_bk1600_ultra_polls_each_remaining_documented_read_point(
    point: int,
) -> None:
    api = RecordingAPI()
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": MODEL}
    coordinator.api = api

    data = await coordinator._async_update_data()

    assert point in {requested for batch in api.batches for requested in batch}
    assert data[str(point)] == point
