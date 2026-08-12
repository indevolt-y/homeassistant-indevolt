"""Existing work-mode and real-time-control write commands."""

from __future__ import annotations

from enum import IntEnum

from .request import OpenDataWrite, write_values


class WorkMode(IntEnum):
    """Raw values currently written for device work mode."""

    SELF_CONSUMED_PRIORITIZED = 1
    REAL_TIME_CONTROL = 4
    CHARGE_DISCHARGE_SCHEDULE = 5


class RealTimeControlState(IntEnum):
    """Raw values currently written for real-time control state."""

    STANDBY = 0
    CHARGING = 1
    DISCHARGING = 2


def set_work_mode(mode: WorkMode) -> OpenDataWrite:
    """Set device work mode."""
    return write_values(47005, mode)


def set_real_time_control_state(state: RealTimeControlState) -> OpenDataWrite:
    """Set only the real-time control state."""
    return write_values(47015, state)


def set_real_time_control_parameters(
    state: RealTimeControlState,
    power: int,
    soc: int,
) -> OpenDataWrite:
    """Set state, power, and target SOC in the existing Action payload."""
    return write_values(47015, state, power, soc)
