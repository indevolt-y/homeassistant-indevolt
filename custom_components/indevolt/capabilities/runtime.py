"""Runtime helpers for documented OpenData read capabilities."""

from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .definitions import GetUserCapability, SetUserCapability


def capabilities_for_model(device_model: str) -> tuple[GetUserCapability, ...]:
    """Keep the historical BK substring route and non-BK fallback route."""
    from .reads import BK_GET_USER_CAPABILITIES, GET_USER_CAPABILITIES

    if "BK1600" in device_model:
        return BK_GET_USER_CAPABILITIES
    return GET_USER_CAPABILITIES


def controls_for_model(device_model: str) -> tuple[SetUserCapability, ...]:
    """Expose new controls only on the historical non-BK fallback route."""
    from .controls import SET_USER_CAPABILITIES

    if "BK1600" in device_model:
        return ()
    return tuple(item for item in SET_USER_CAPABILITIES if item.user_visible)


def is_returned(data: dict[str, Any], capability: GetUserCapability) -> bool:
    """Create a new entity only when its first response contains a value."""
    return data.get(str(capability.point)) is not None


def is_control_returned(data: dict[str, Any], capability: SetUserCapability) -> bool:
    """Apply the explicit first-response creation rule for a new control."""
    if not capability.create_requires_read_value:
        return True
    return (
        capability.read_point is not None
        and data.get(str(capability.read_point)) is not None
    )


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


def encode_time(value: time) -> int:
    """Encode a Home Assistant time into the protocol's hour/minute word."""
    if value.second or value.microsecond:
        raise ServiceValidationError("OpenData time values support whole minutes only")
    return value.hour << 8 | value.minute


async def async_write_control(
    coordinator: Any,
    capability: SetUserCapability,
    value: int | float,
) -> None:
    """Write one new control and report rejection without changing old controls."""
    try:
        accepted = await coordinator.api.set_data(
            point=capability.point,
            value=[value],
        )
    except Exception as err:
        raise HomeAssistantError(
            f"Unable to write OpenData point {capability.point}: {err}"
        ) from err

    if not accepted:
        raise HomeAssistantError(f"Device rejected OpenData point {capability.point}")

    await coordinator.async_refresh()


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
