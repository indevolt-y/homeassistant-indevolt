"""Contracts for model-specific OpenData response schemas."""

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
    response = importlib.import_module("opendata.response")
finally:
    sys.path.pop(0)

BK1600_SCHEMA = response.BK1600_SCHEMA
BK1600_ULTRA_SCHEMA = response.BK1600_ULTRA_SCHEMA
FALLBACK_SCHEMA = response.FALLBACK_SCHEMA
PF2000_SCHEMA = response.PF2000_SCHEMA
SF2000_SCHEMA = response.SF2000_SCHEMA
OpenDataField = response.OpenDataField

BK1600_POLLING_BASELINE = (
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

SF2000_POLLING_BASELINE = (
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


def points(fields: tuple[OpenDataField, ...]) -> tuple[int, ...]:
    """Return the ordered point contract represented by response fields."""
    return tuple(field.point for field in fields)


def test_response_field_is_immutable_and_comparable() -> None:
    field = OpenDataField(point=1501, response_key="1501")

    assert tuple(item.name for item in dataclass_fields(OpenDataField)) == (
        "point",
        "response_key",
    )
    assert field == OpenDataField(point=1501, response_key="1501")
    assert hash(field) == hash(OpenDataField(point=1501, response_key="1501"))

    with pytest.raises(FrozenInstanceError):
        field.point = 1502


def test_response_schema_imports_without_home_assistant() -> None:
    """The schema must remain importable as part of an extractable package."""
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
assert "opendata.response" not in sys.modules
from opendata.response import (
    BK1600_SCHEMA,
    BK1600_ULTRA_SCHEMA,
    FALLBACK_SCHEMA,
    PF2000_SCHEMA,
    SF2000_SCHEMA,
)
assert len(BK1600_SCHEMA) == 19
assert BK1600_ULTRA_SCHEMA is BK1600_SCHEMA
assert len(SF2000_SCHEMA) == 98
assert PF2000_SCHEMA is SF2000_SCHEMA
assert FALLBACK_SCHEMA is SF2000_SCHEMA
"""

    subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("schema", "baseline"),
    [
        (BK1600_SCHEMA, BK1600_POLLING_BASELINE),
        (BK1600_ULTRA_SCHEMA, BK1600_POLLING_BASELINE),
        (SF2000_SCHEMA, SF2000_POLLING_BASELINE),
        (PF2000_SCHEMA, SF2000_POLLING_BASELINE),
        (FALLBACK_SCHEMA, SF2000_POLLING_BASELINE),
    ],
)
def test_each_model_entry_preserves_its_current_polling_order(
    schema: tuple[OpenDataField, ...],
    baseline: tuple[int, ...],
) -> None:
    assert points(schema) == baseline
    assert len(set(points(schema))) == len(schema)


def test_confirmed_model_pairs_share_one_point_table() -> None:
    assert BK1600_ULTRA_SCHEMA is BK1600_SCHEMA
    assert PF2000_SCHEMA is SF2000_SCHEMA


def test_unspecified_models_fall_back_to_the_sf2000_point_table() -> None:
    assert FALLBACK_SCHEMA is SF2000_SCHEMA


def test_only_model_and_fallback_schema_entries_are_exposed() -> None:
    schema_names = {name for name in vars(response) if name.endswith("_SCHEMA")}

    assert schema_names == {
        "BK1600_SCHEMA",
        "BK1600_ULTRA_SCHEMA",
        "FALLBACK_SCHEMA",
        "PF2000_SCHEMA",
        "SF2000_SCHEMA",
    }


@pytest.mark.parametrize(
    "fields",
    [BK1600_SCHEMA, BK1600_ULTRA_SCHEMA, SF2000_SCHEMA, PF2000_SCHEMA],
)
def test_response_keys_only_capture_the_proven_wire_key(
    fields: tuple[OpenDataField, ...],
) -> None:
    assert all(field.response_key == str(field.point) for field in fields)
