"""Acceptance tests for every new OpenData SetData point."""

from __future__ import annotations

from typing import Any

import pytest

from custom_components.indevolt.opendata import IndevoltAPI
from tests.models._opendata_point_additions import (
    ADDITIONAL_DEFAULT_READ_POINTS,
    ADDITIONAL_DEFAULT_SET_CASES,
    ADDITIONAL_DEFAULT_SET_POINTS,
    BASELINE_DEFAULT_SET_POINTS,
    SetPointCase,
)


class FakeResponse:
    """Successful SetData response used by the transport contract."""

    status = 200

    async def json(self) -> dict[str, bool]:
        return {"result": True}


class FakeRequestContext:
    """Async context manager returned by the fake session."""

    async def __aenter__(self) -> FakeResponse:
        return FakeResponse()

    async def __aexit__(self, *args: Any) -> None:
        return None


class RecordingSession:
    """Record the exact URL generated for one documented write."""

    def __init__(self) -> None:
        self.urls: list[str] = []

    def post(self, url: str, **kwargs: Any) -> FakeRequestContext:
        self.urls.append(url)
        return FakeRequestContext()


def test_additional_set_point_evidence_is_complete_and_unambiguous() -> None:
    """The corrected table has 63 additional SF/PF writes and no baseline write."""
    assert len(ADDITIONAL_DEFAULT_SET_CASES) == 63
    assert len(set(ADDITIONAL_DEFAULT_SET_POINTS)) == 63
    assert set(ADDITIONAL_DEFAULT_SET_POINTS).isdisjoint(BASELINE_DEFAULT_SET_POINTS)


def test_simulated_load_set_points_cover_all_48_half_hour_slots() -> None:
    """The documented schedule block is complete and contiguous."""
    load_points = tuple(
        case.point
        for case in ADDITIONAL_DEFAULT_SET_CASES
        if case.description.startswith("simulated load time slot")
    )
    assert load_points == tuple(range(12197, 12245))


def test_get_and_set_additions_remain_separate_protocol_lists() -> None:
    """Only the three documented read/write additions appear in both lists."""
    assert set(ADDITIONAL_DEFAULT_READ_POINTS) & set(ADDITIONAL_DEFAULT_SET_POINTS) == {
        4,
        35001,
        35002,
    }


@pytest.mark.parametrize(
    "case",
    ADDITIONAL_DEFAULT_SET_CASES,
    ids=lambda case: f"point_{case.point}",
)
@pytest.mark.asyncio
async def test_each_additional_set_point_reaches_the_http_api(
    case: SetPointCase,
) -> None:
    """A documented point and scalar are preserved in the SetData request."""
    session = RecordingSession()
    api = IndevoltAPI("192.0.2.10", 8080, session)  # type: ignore[arg-type]

    result = await api.set_data(case.point, [case.transport_value])

    assert result is True
    assert session.urls == [
        "http://192.0.2.10:8080/rpc/Indevolt.SetData?"
        f'config={{"f":16,"t":{case.point},"v":[{case.transport_value}]}}'
    ]
