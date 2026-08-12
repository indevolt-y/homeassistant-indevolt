"""Existing power and state-of-charge write commands."""

from __future__ import annotations

from .request import OpenDataWrite, write_values


def set_backup_soc(value: int) -> OpenDataWrite:
    """Set the backup state-of-charge target."""
    return write_values(1142, value)


def set_inverter_input_limit(value: int) -> OpenDataWrite:
    """Set the inverter input power limit."""
    return write_values(1138, value)


def set_max_ac_output_power(value: int) -> OpenDataWrite:
    """Set the maximum AC output power."""
    return write_values(1147, value)


def set_feed_in_power_limit(value: int) -> OpenDataWrite:
    """Set the feed-in power limit."""
    return write_values(1146, value)


def set_real_time_control_power(value: int) -> OpenDataWrite:
    """Set real-time control power."""
    return write_values(47016, value)


def set_real_time_control_target_soc(value: int) -> OpenDataWrite:
    """Set the real-time control target state of charge."""
    return write_values(47017, value)
