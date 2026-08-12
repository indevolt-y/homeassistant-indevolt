"""Contracts for the ordered polling baselines copied from commit 96ca128."""

from __future__ import annotations

import importlib
import subprocess
import sys
from dataclasses import FrozenInstanceError
from dataclasses import fields as dataclass_fields
from pathlib import Path

import pytest

OPEN_DATA_PACKAGE = (
    Path(__file__).parents[3] / "custom_components" / "indevolt" / "opendata"
)
sys.path.insert(0, str(OPEN_DATA_PACKAGE.parent))
try:
    polling = importlib.import_module("opendata.polling")
finally:
    sys.path.pop(0)

BK_POLLING_BASELINE = polling.BK_POLLING_BASELINE
DEFAULT_POLLING_BASELINE = polling.DEFAULT_POLLING_BASELINE
PollingField = polling.PollingField

BK_96CA128_POINTS = (
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

DEFAULT_96CA128_POINTS = (
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


def points(fields: tuple[PollingField, ...]) -> tuple[int, ...]:
    """Return the ordered points represented by a polling baseline."""
    return tuple(field.point for field in fields)


def batches(point_sequence: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Split points at the coordinator's unchanged eight-point boundary."""
    return tuple(
        point_sequence[offset : offset + 8]
        for offset in range(0, len(point_sequence), 8)
    )


def test_polling_field_is_immutable_and_comparable() -> None:
    field = PollingField(point=1501, response_key="1501")

    assert tuple(item.name for item in dataclass_fields(PollingField)) == (
        "point",
        "response_key",
    )
    assert field == PollingField(point=1501, response_key="1501")
    assert hash(field) == hash(PollingField(point=1501, response_key="1501"))

    with pytest.raises(FrozenInstanceError):
        field.point = 1502


def test_polling_baselines_import_without_home_assistant() -> None:
    """The baselines must remain importable as part of an extractable package."""
    script = f"""
import builtins
import sys

original_import = builtins.__import__

def guarded_import(name, *args, **kwargs):
    if name == "homeassistant" or name.startswith("homeassistant."):
        raise AssertionError(f"unexpected Home Assistant import: {{name}}")
    return original_import(name, *args, **kwargs)

builtins.__import__ = guarded_import
sys.path.insert(0, {str(OPEN_DATA_PACKAGE.parent)!r})
import opendata
assert "opendata.polling" not in sys.modules
from opendata.polling import (
    BK_POLLING_BASELINE,
    DEFAULT_POLLING_BASELINE,
)
assert len(BK_POLLING_BASELINE) == 19
assert len(DEFAULT_POLLING_BASELINE) == 98
"""

    subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("baseline", "expected_points"),
    [
        (BK_POLLING_BASELINE, BK_96CA128_POINTS),
        (DEFAULT_POLLING_BASELINE, DEFAULT_96CA128_POINTS),
    ],
)
def test_each_baseline_preserves_the_96ca128_polling_order(
    baseline: tuple[PollingField, ...],
    expected_points: tuple[int, ...],
) -> None:
    assert points(baseline) == expected_points
    assert len(set(points(baseline))) == len(baseline)


def test_baselines_preserve_the_96ca128_eight_point_batches() -> None:
    assert batches(points(BK_POLLING_BASELINE)) == batches(BK_96CA128_POINTS)
    assert batches(points(DEFAULT_POLLING_BASELINE)) == batches(DEFAULT_96CA128_POINTS)
    assert tuple(map(len, batches(points(BK_POLLING_BASELINE)))) == (8, 8, 3)
    assert tuple(map(len, batches(points(DEFAULT_POLLING_BASELINE)))) == (
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        2,
    )


def test_only_the_two_historical_branch_baselines_are_defined() -> None:
    baseline_names = {
        name for name in vars(polling) if name.endswith("_POLLING_BASELINE")
    }

    assert set(polling.__all__) == {
        "BK_POLLING_BASELINE",
        "DEFAULT_POLLING_BASELINE",
        "PollingField",
    }
    assert baseline_names == {
        "BK_POLLING_BASELINE",
        "DEFAULT_POLLING_BASELINE",
    }
    assert not any(name.endswith("_SCHEMA") for name in vars(polling))


@pytest.mark.parametrize(
    "fields",
    [BK_POLLING_BASELINE, DEFAULT_POLLING_BASELINE],
)
def test_response_keys_only_copy_the_existing_wire_key(
    fields: tuple[PollingField, ...],
) -> None:
    assert all(field.response_key == str(field.point) for field in fields)
