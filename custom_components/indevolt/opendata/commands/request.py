"""Generic OpenData SetData request representation and encoding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class SetDataRequest(TypedDict):
    """Keyword arguments accepted by ``IndevoltAPI.set_data``."""

    point: int
    value: list[int]


@dataclass(frozen=True, slots=True)
class OpenDataWrite:
    """An immutable protocol write ready to pass to the OpenData client."""

    point: int
    value: tuple[int, ...]

    def as_set_data_request(self) -> SetDataRequest:
        """Return a fresh request using the client's existing list payload."""
        return {"point": self.point, "value": list(self.value)}


def write_values(point: int, *values: int) -> OpenDataWrite:
    """Build a write from one or more raw integer protocol values."""
    if not values:
        raise ValueError("an OpenData write requires at least one value")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise TypeError("OpenData protocol values must be integers")

    return OpenDataWrite(
        point=point,
        value=tuple(int(value) for value in values),
    )


def write_boolean(point: int, active: bool) -> OpenDataWrite:
    """Encode the existing boolean protocol convention as ``1`` or ``0``."""
    if not isinstance(active, bool):
        raise TypeError("an OpenData boolean write requires a boolean value")
    return OpenDataWrite(point=point, value=(int(active),))
