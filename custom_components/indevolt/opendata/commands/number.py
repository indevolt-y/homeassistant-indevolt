"""Existing OpenData writes used by Home Assistant Number entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

NumberValue = int | float


class SetDataRequest(TypedDict):
    """Keyword arguments accepted by ``IndevoltAPI.set_data`` at runtime."""

    point: int
    value: list[NumberValue]


@dataclass(frozen=True, slots=True)
class NumberWrite:
    """One existing Number write without validation or value conversion."""

    point: int
    value: NumberValue

    def as_set_data_request(self) -> SetDataRequest:
        """Return the exact single-value list used by the existing Number path."""
        return {"point": self.point, "value": [self.value]}


def set_backup_soc(value: NumberValue) -> NumberWrite:
    """Build the existing backup SOC write."""
    return NumberWrite(point=1142, value=value)


def set_inverter_input_limit(value: NumberValue) -> NumberWrite:
    """Build the existing inverter input limit write."""
    return NumberWrite(point=1138, value=value)


def set_max_ac_output_power(value: NumberValue) -> NumberWrite:
    """Build the existing maximum AC output power write."""
    return NumberWrite(point=1147, value=value)


def set_feed_in_power_limit(value: NumberValue) -> NumberWrite:
    """Build the existing feed-in power limit write."""
    return NumberWrite(point=1146, value=value)


def set_real_time_control_power(value: NumberValue) -> NumberWrite:
    """Build the existing real-time control power write."""
    return NumberWrite(point=47016, value=value)


def set_real_time_control_target_soc(value: NumberValue) -> NumberWrite:
    """Build the existing real-time control target SOC write."""
    return NumberWrite(point=47017, value=value)
