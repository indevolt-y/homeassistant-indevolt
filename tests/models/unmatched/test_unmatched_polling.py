"""Polling fallback for a model that matches no known family."""

from __future__ import annotations

import pytest

from custom_components.indevolt.coordinator import IndevoltDeviceUpdateCoordinator

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

    points = {point for batch in api.batches for point in batch}
    assert [len(batch) for batch in api.batches] == ([8] * 12) + [2]
    assert len(points) == 98
    assert {142, 7171, 9032, 9051, 9070, 9165, 9218, 19177} <= points
    assert 21028 not in points
    assert set(data) == {str(point) for point in points}
