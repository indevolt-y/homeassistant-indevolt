"""Contracts for existing power and state-of-charge writes."""

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
    power = importlib.import_module("opendata.commands.power")
finally:
    sys.path.pop(0)


@pytest.mark.parametrize(
    ("builder", "value", "point"),
    [
        (power.set_backup_soc, 80, 1142),
        (power.set_inverter_input_limit, 2400, 1138),
        (power.set_max_ac_output_power, 2400, 1147),
        (power.set_feed_in_power_limit, 800, 1146),
        (power.set_real_time_control_power, 1200, 47016),
        (power.set_real_time_control_target_soc, 80, 47017),
    ],
)
def test_power_command_preserves_existing_point_and_payload(
    builder,
    value: int,
    point: int,
) -> None:
    assert builder(value).as_set_data_request() == {
        "point": point,
        "value": [value],
    }
