"""Contracts for existing load and switch-like device writes."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

OPEN_DATA_PACKAGE = (
    Path(__file__).parents[4] / "custom_components" / "indevolt" / "opendata"
)
sys.path.insert(0, str(OPEN_DATA_PACKAGE.parent))
try:
    device = importlib.import_module("opendata.commands.device")
finally:
    sys.path.pop(0)


def test_load_enum_and_existing_point_one_write_are_preserved() -> None:
    assert {item.name: item.value for item in device.LoadSetting} == {
        "SMART_PLUG": 1,
        "METER": 2,
        "KEY_LOAD": 3,
        "CUSTOM": 4,
    }
    write = device.set_load_setting(device.LoadSetting.KEY_LOAD)
    assert write.as_set_data_request() == {"point": 1, "value": [3]}


@pytest.mark.parametrize(
    ("builder", "point"),
    [
        (device.set_light, 7265),
        (device.set_grid_charging, 1143),
        (device.set_bypass, 7266),
    ],
)
def test_switch_like_commands_preserve_points_and_boolean_encoding(
    builder,
    point: int,
) -> None:
    assert builder(True).as_set_data_request() == {"point": point, "value": [1]}
    assert builder(False).as_set_data_request() == {"point": point, "value": [0]}
