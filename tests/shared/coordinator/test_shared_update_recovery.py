"""Regression tests for coordinator polling and transient failures."""

from __future__ import annotations

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.indevolt.coordinator import IndevoltDeviceUpdateCoordinator


class RecordingAPI:
    """Record requested point batches and optionally fail the next request."""

    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.batches = []

    async def fetch_data(self, batch):
        self.batches.append(list(batch))
        if self.failures:
            self.failures -= 1
            raise RuntimeError("temporary polling failure")
        return {str(point): point for point in batch}


def make_coordinator(model: str, api: RecordingAPI):
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = {"device_model": model}
    coordinator.api = api
    return coordinator


@pytest.mark.asyncio
async def test_coordinator_recovers_on_poll_after_transient_update_failure() -> None:
    api = RecordingAPI(failures=1)
    coordinator = make_coordinator("PowerFlex2000", api)

    with pytest.raises(UpdateFailed, match="temporary polling failure") as error:
        await coordinator._async_update_data()

    assert isinstance(error.value.__cause__, RuntimeError)

    data = await coordinator._async_update_data()

    successful_batches = api.batches[1:]
    assert successful_batches
    assert data == {
        str(point): point
        for batch in successful_batches
        for point in batch
    }
