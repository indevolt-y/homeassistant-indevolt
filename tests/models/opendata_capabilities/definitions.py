"""Shared definitions for test-side OpenData user capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

GetDomain = Literal["sensor", "binary_sensor", "number", "time"]
SetExposure = Literal[
    "number",
    "select",
    "time",
    "existing_select_extension",
    "existing_control_transport",
    "external_data_injection",
]

# A write capability cannot be inferred from an old readable counterpart alone.
# Tests use this newly documented protocol-version point as the reviewable gate;
# a device that does not return it keeps the complete baseline user experience.
CONTROL_CAPABILITY_MARKER_POINT = 1127


@dataclass(frozen=True, slots=True)
class GetUserCapability:
    """One guessed entity a user can see after a point is returned."""

    point: int
    domain: GetDomain
    key: str
    name: str
    sample_value: Any
    expected_state: str
    scope: str = "main"
    unit: str | None = None
    enabled_by_default: bool = True

    def unique_id(self, serial: str) -> str:
        """Return the expected stable unique ID for this guessed entity."""
        if self.scope.startswith("battery_"):
            pack_id = self.scope.removeprefix("battery_")
            return f"{serial}_battery_{pack_id}_{self.key}"
        return f"{serial}_{self.key}"


@dataclass(frozen=True, slots=True)
class SetUserCapability:
    """One guessed user control or an explicitly non-user write."""

    point: int
    exposure: SetExposure
    name: str
    key: str | None = None
    user_value: Any = None
    wire_value: int | float | None = None
    read_point: int | None = None
    expected_initial_state: str | None = None
    enabled_by_default: bool = True
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    unit: str | None = None
    options: tuple[str, ...] = ()

    @property
    def user_visible(self) -> bool:
        return self.exposure in {
            "number",
            "select",
            "time",
            "existing_select_extension",
        }

    @property
    def entity_domain(self) -> str | None:
        if self.exposure == "existing_select_extension":
            return "select"
        if self.exposure in {"number", "select", "time"}:
            return self.exposure
        return None
