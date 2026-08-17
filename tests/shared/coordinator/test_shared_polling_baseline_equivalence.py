"""End-to-end equivalence tests for the extracted polling baselines."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.indevolt.coordinator import IndevoltDeviceUpdateCoordinator

BK_MAIN_POINTS = (
    1501,
    1502,
    1505,
    1664,
    1665,
    2101,
    2107,
    2108,
    6000,
    6001,
    6002,
    6004,
    6005,
    6006,
    6007,
    6105,
    7101,
    7120,
    21028,
)

DEFAULT_MAIN_POINTS = (
    142,
    606,
    667,
    680,
    1118,
    1109,
    1119,
    1120,
    1136,
    1137,
    1138,
    1139,
    1140,
    1141,
    1142,
    1143,
    1098,
    1099,
    1501,
    1502,
    1600,
    1601,
    1602,
    1603,
    1632,
    1633,
    1634,
    1635,
    1664,
    1665,
    1666,
    1667,
    2101,
    2104,
    2105,
    2107,
    2108,
    2600,
    2612,
    2618,
    6000,
    6001,
    6002,
    6004,
    6005,
    6006,
    6007,
    6105,
    7101,
    7120,
    7171,
    9000,
    9004,
    9008,
    9009,
    9011,
    9012,
    9013,
    9016,
    9020,
    9021,
    9023,
    9030,
    9032,
    9035,
    9039,
    9040,
    9042,
    9049,
    9051,
    9054,
    9058,
    9059,
    9061,
    9068,
    9070,
    9149,
    9153,
    9154,
    9156,
    9163,
    9165,
    9202,
    9206,
    9216,
    9218,
    9219,
    9222,
    11009,
    11010,
    11011,
    11016,
    11034,
    19173,
    19174,
    19175,
    19176,
    19177,
)


def expected_batches(points: tuple[int, ...]) -> list[list[int]]:
    """Copy the unchanged eight-point batching used by local MAIN."""
    return [list(points[offset : offset + 8]) for offset in range(0, len(points), 8)]


class RecordingAPI:
    """Record requests and return deterministic, overlapping responses."""

    def __init__(self, *, fail_on_request: int | None = None) -> None:
        self.fail_on_request = fail_on_request
        self.batches: list[list[int]] = []

    async def fetch_data(self, batch: list[int]) -> Mapping[str, Any]:
        self.batches.append(list(batch))
        request_number = len(self.batches)
        if request_number == self.fail_on_request:
            raise RuntimeError("polling failure")

        return {
            "last_batch": request_number,
            **{str(point): point for point in batch},
        }


def make_coordinator(
    config: dict[str, Any], api: RecordingAPI
) -> IndevoltDeviceUpdateCoordinator:
    """Build only the state exercised by _async_update_data()."""
    coordinator = object.__new__(IndevoltDeviceUpdateCoordinator)
    coordinator.config = config
    coordinator.api = api
    return coordinator


@pytest.mark.parametrize(
    ("device_model", "expected_points"),
    [
        ("BK1600/BK1600Ultra", BK_MAIN_POINTS),
        ("prefix-BK1600-suffix", BK_MAIN_POINTS),
        ("SolidFlex/PowerFlex2000", DEFAULT_MAIN_POINTS),
        ("value-without-the-BK-marker", DEFAULT_MAIN_POINTS),
    ],
)
@pytest.mark.asyncio
async def test_coordinator_requests_and_merges_exactly_as_main(
    device_model: str, expected_points: tuple[int, ...]
) -> None:
    api = RecordingAPI()
    coordinator = make_coordinator({"device_model": device_model}, api)

    data = await coordinator._async_update_data()

    main_batches = expected_batches(expected_points)
    assert api.batches[: len(main_batches)] == main_batches
    assert {key: data[key] for key in map(str, expected_points)} == {
        str(point): point for point in expected_points
    }


@pytest.mark.asyncio
async def test_coordinator_stops_at_the_same_failing_batch_as_main() -> None:
    api = RecordingAPI(fail_on_request=2)
    coordinator = make_coordinator({"device_model": "SolidFlex/PowerFlex2000"}, api)

    with pytest.raises(UpdateFailed, match="^Update failed: polling failure$") as error:
        await coordinator._async_update_data()

    assert isinstance(error.value.__cause__, RuntimeError)
    assert api.batches == expected_batches(DEFAULT_MAIN_POINTS)[:2]


@pytest.mark.parametrize(
    ("device_model", "baseline_points"),
    [
        ("BK1600/BK1600Ultra", BK_MAIN_POINTS),
        ("SolidFlex/PowerFlex2000", DEFAULT_MAIN_POINTS),
    ],
)
@pytest.mark.asyncio
async def test_additional_batch_failure_keeps_complete_baseline_snapshot(
    device_model: str,
    baseline_points: tuple[int, ...],
) -> None:
    baseline_batches = expected_batches(baseline_points)
    api = RecordingAPI(fail_on_request=len(baseline_batches) + 2)
    coordinator = make_coordinator({"device_model": device_model}, api)

    data = await coordinator._async_update_data()

    assert api.batches[: len(baseline_batches)] == baseline_batches
    assert data == {
        "last_batch": len(baseline_batches),
        **{str(point): point for point in baseline_points},
    }


@pytest.mark.parametrize(
    ("config", "cause_type"),
    [
        ({}, KeyError),
        ({"device_model": None}, TypeError),
    ],
)
@pytest.mark.asyncio
async def test_coordinator_preserves_invalid_saved_value_failures(
    config: dict[str, Any], cause_type: type[Exception]
) -> None:
    api = RecordingAPI()
    coordinator = make_coordinator(config, api)

    with pytest.raises(UpdateFailed) as error:
        await coordinator._async_update_data()

    assert isinstance(error.value.__cause__, cause_type)
    assert api.batches == []
