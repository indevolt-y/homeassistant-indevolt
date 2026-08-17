"""Shared definitions for test-side OpenData user capabilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import time
from typing import Any, Literal

from homeassistant.components.number import NumberMode
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import EntityCategory

GetDomain = Literal["sensor", "binary_sensor", "number", "time"]
SetExposure = Literal[
    "number",
    "select",
    "time",
    "existing_control_transport",
    "external_data_injection",
]


@dataclass(frozen=True, slots=True)
class GetUserCapability:
    """One guessed entity and the documented meaning of its raw values."""

    point: int
    domain: GetDomain
    key: str
    name: str
    translation_key: str
    sample_value: Any
    expected_state: str
    translation_placeholders: Mapping[str, str] | None = None
    scope: str = "main"
    unit: str | None = None
    device_class: str | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None
    suggested_display_precision: int | None = None
    icon: str | None = None
    options: tuple[str, ...] = ()
    enabled_by_default: bool = True
    create_requires_value: bool = True
    additional_state_cases: tuple[tuple[Any, str], ...] = ()

    @property
    def native_value_type(self) -> type | tuple[type, ...]:
        """Return the native Python type Home Assistant should receive."""
        if self.domain == "binary_sensor":
            return bool
        if self.domain == "time":
            return time
        if self.domain == "number":
            return (int, float)
        if self.device_class == "enum" or isinstance(self.sample_value, (str, tuple)):
            return str
        try:
            float(self.expected_state)
        except ValueError:
            return str
        return (int, float)

    @property
    def state_cases(self) -> tuple[tuple[Any, str], ...]:
        """Return every raw OpenData value and expected HA state to verify."""
        return (
            (self.sample_value, self.expected_state),
            *self.additional_state_cases,
        )

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
    translation_key: str | None = None
    translation_placeholders: Mapping[str, str] | None = None
    device_class: str | None = None
    entity_category: EntityCategory | None = None
    mode: NumberMode | None = None
    icon: str | None = None
    key: str | None = None
    user_value: Any = None
    wire_value: int | float | None = None
    integer_wire_value: bool = False
    read_point: int | None = None
    read_sample_value: Any = None
    expected_initial_state: str | None = None
    enabled_by_default: bool = True
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    unit: str | None = None
    options: tuple[str, ...] = ()
    create_requires_read_value: bool = True

    @property
    def user_visible(self) -> bool:
        return self.exposure in {
            "number",
            "select",
            "time",
        }

    @property
    def entity_domain(self) -> str | None:
        if self.exposure in {"number", "select", "time"}:
            return self.exposure
        return None

    @property
    def native_value_type(self) -> type | tuple[type, ...]:
        """Return the native Python type Home Assistant should receive."""
        if self.entity_domain == "number":
            return (int, float)
        if self.entity_domain == "time":
            return time
        if self.entity_domain == "select":
            return str
        raise ValueError(f"point {self.point} does not create a Home Assistant entity")
