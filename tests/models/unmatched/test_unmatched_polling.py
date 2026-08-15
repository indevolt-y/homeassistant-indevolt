"""Polling fallback for a model that matches no known family."""

from __future__ import annotations

import pytest

from custom_components.indevolt.coordinator import IndevoltDeviceUpdateCoordinator
from tests.models._opendata_point_additions import (
    BASELINE_DEFAULT_POINT_BATCHES,
    DEFAULT_CAPABILITY_POINT_BATCHES,
    DEFAULT_CAPABILITY_READ_POINTS,
    DEFAULT_NON_USER_READ_POINTS,
    REMAINING_DEFAULT_USER_READ_POINTS,
    flattened,
)

MODEL = "FutureModel"


class RecordingAPI:
    def __init__(self) -> None:
        self.batches = []

    async def fetch_data(self, batch):
        self.batches.append(list(batch))
        return {str(point): point for point in batch}


@pytest.mark.asyncio
async def test_unmatched_model_polls_the_gen2_fallback_contract() -> None:
    api = RecordingAPI()
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": MODEL}
    coordinator.api = api

    data = await coordinator._async_update_data()

    expected_batches = (
        BASELINE_DEFAULT_POINT_BATCHES
        + DEFAULT_CAPABILITY_POINT_BATCHES
        + (REMAINING_DEFAULT_USER_READ_POINTS,)
    )
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
async def test_unmatched_model_keeps_additional_points_on_default_route(
    point: int,
) -> None:
    """The established non-BK fallback must not lose a documented addition."""
    api = RecordingAPI()
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": MODEL}
    coordinator.api = api

    data = await coordinator._async_update_data()

    assert point in {requested for batch in api.batches for requested in batch}
    assert data[str(point)] == point


@pytest.mark.parametrize(
    "point",
    REMAINING_DEFAULT_USER_READ_POINTS,
    ids=lambda point: f"point_{point}",
)
@pytest.mark.asyncio
async def test_unmatched_model_keeps_each_remaining_documented_read_point(
    point: int,
) -> None:
    api = RecordingAPI()
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": MODEL}
    coordinator.api = api

    data = await coordinator._async_update_data()

    assert point in {requested for batch in api.batches for requested in batch}
    assert data[str(point)] == point


@pytest.mark.parametrize("point", DEFAULT_NON_USER_READ_POINTS)
@pytest.mark.asyncio
async def test_unmatched_model_does_not_poll_duplicate_non_user_read_point(
    point: int,
) -> None:
    api = RecordingAPI()
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": MODEL}
    coordinator.api = api

    data = await coordinator._async_update_data()

    assert point not in {requested for batch in api.batches for requested in batch}
    assert str(point) not in data
