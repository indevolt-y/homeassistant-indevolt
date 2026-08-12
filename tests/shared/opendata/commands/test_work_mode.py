"""Contracts for existing work-mode and real-time-control writes."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

OPEN_DATA_PACKAGE = (
    Path(__file__).parents[4] / "custom_components" / "indevolt" / "opendata"
)
sys.path.insert(0, str(OPEN_DATA_PACKAGE.parent))
try:
    work_mode = importlib.import_module("opendata.commands.work_mode")
finally:
    sys.path.pop(0)


def test_protocol_enums_preserve_existing_raw_values() -> None:
    assert {item.name: item.value for item in work_mode.WorkMode} == {
        "SELF_CONSUMED_PRIORITIZED": 1,
        "REAL_TIME_CONTROL": 4,
        "CHARGE_DISCHARGE_SCHEDULE": 5,
    }
    assert {item.name: item.value for item in work_mode.RealTimeControlState} == {
        "STANDBY": 0,
        "CHARGING": 1,
        "DISCHARGING": 2,
    }


def test_work_mode_write_preserves_point_and_single_value_payload() -> None:
    write = work_mode.set_work_mode(work_mode.WorkMode.REAL_TIME_CONTROL)
    assert write.as_set_data_request() == {"point": 47005, "value": [4]}


def test_point_47015_keeps_its_two_distinct_payload_shapes() -> None:
    state_write = work_mode.set_real_time_control_state(
        work_mode.RealTimeControlState.DISCHARGING
    )
    parameters_write = work_mode.set_real_time_control_parameters(
        work_mode.RealTimeControlState.CHARGING,
        1200,
        80,
    )

    assert state_write.as_set_data_request() == {"point": 47015, "value": [2]}
    assert parameters_write.as_set_data_request() == {
        "point": 47015,
        "value": [1, 1200, 80],
    }
