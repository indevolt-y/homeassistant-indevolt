"""Contracts copied from the six existing Number write callbacks."""

from __future__ import annotations

import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

OPEN_DATA_PACKAGE = (
    Path(__file__).parents[4] / "custom_components" / "indevolt" / "opendata"
)
sys.path.insert(0, str(OPEN_DATA_PACKAGE.parent))
try:
    number_commands = importlib.import_module("opendata.commands.number")
finally:
    sys.path.pop(0)


@pytest.mark.parametrize(
    ("builder", "value", "point"),
    [
        (number_commands.set_backup_soc, 80.0, 1142),
        (number_commands.set_inverter_input_limit, 2400.0, 1138),
        (number_commands.set_max_ac_output_power, 2400.0, 1147),
        (number_commands.set_feed_in_power_limit, 800.0, 1146),
        (number_commands.set_real_time_control_power, 1200.0, 47016),
        (number_commands.set_real_time_control_target_soc, 80.0, 47017),
    ],
)
def test_number_commands_preserve_point_value_and_float_type(
    builder,
    value: float,
    point: int,
) -> None:
    request = builder(value).as_set_data_request()

    assert request == {"point": point, "value": [value]}
    assert type(request["value"][0]) is float


@pytest.mark.parametrize("value", [0, 1200, 1200.0, -1.0, 10801.0, True])
def test_number_command_adds_no_validation_or_conversion(value) -> None:
    request = number_commands.set_real_time_control_power(value).as_set_data_request()

    assert request["value"][0] is value


def test_number_write_is_immutable_and_returns_a_fresh_list() -> None:
    write = number_commands.set_real_time_control_power(1200.0)

    with pytest.raises(FrozenInstanceError):
        write.point = 47015

    first_request = write.as_set_data_request()
    first_request["value"].append(80.0)

    assert write.as_set_data_request() == {"point": 47016, "value": [1200.0]}
