"""Runtime helpers for documented OpenData read capabilities."""

from __future__ import annotations

from datetime import time
from typing import Any

from .definitions import GetUserCapability


def capabilities_for_model(device_model: str) -> tuple[GetUserCapability, ...]:
    """Keep the historical BK substring route and non-BK fallback route."""
    from .reads import BK_GET_USER_CAPABILITIES, GET_USER_CAPABILITIES

    if "BK1600" in device_model:
        return BK_GET_USER_CAPABILITIES
    return GET_USER_CAPABILITIES


def is_returned(data: dict[str, Any], capability: GetUserCapability) -> bool:
    """Create a new entity only when its first response contains a value."""
    return data.get(str(capability.point)) is not None


def decode_time(value: Any) -> time | None:
    """Decode the protocol's packed hour/minute value."""
    if value is None:
        return None
    if not isinstance(value, int):
        return None

    hour = value >> 8
    minute = value & 0xFF
    if hour > 23 or minute > 59:
        return None
    return time(hour, minute)


def _decode_device_datetime(value: Any) -> str | None:
    """Decode the three-word device date and time representation."""
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    year_month, day_hour, minute_second = value
    if not all(isinstance(item, int) for item in value):
        return None

    year = 2000 + (year_month >> 8)
    month = year_month & 0xFF
    day = day_hour >> 8
    hour = day_hour & 0xFF
    minute = minute_second >> 8
    second = minute_second & 0xFF
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


def capability_value(capability: GetUserCapability, raw_value: Any) -> Any:
    """Convert one returned OpenData value to its native Home Assistant value."""
    if raw_value is None:
        return None

    if capability.domain == "time":
        return decode_time(raw_value)

    if capability.domain == "binary_sensor":
        states = dict(capability.state_cases)
        state = states.get(raw_value)
        if state is None:
            return None
        return state == "on"

    if capability.options:
        return dict(capability.state_cases).get(raw_value)

    if capability.point == 1127 and isinstance(raw_value, int):
        return f"V{raw_value // 10}.{raw_value % 10}"

    if capability.point == 11008:
        return _decode_device_datetime(raw_value)

    if capability.point == 1505 and isinstance(raw_value, (int, float)):
        return raw_value / 1000

    return raw_value
