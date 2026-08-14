"""Reusable user-behavior harness for OpenData model tests."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from types import ModuleType, SimpleNamespace
from typing import Any

from custom_components.indevolt.const import DOMAIN

from .opendata_capabilities import (
    GET_USER_CAPABILITIES,
    GetUserCapability,
    SetUserCapability,
)

SERIAL = "CAPABILITY-USER-SN"
PACK_SERIAL_POINTS = {
    1: "9032",
    2: "9051",
    3: "9070",
    4: "9165",
    5: "9218",
}
CAPABILITY_DOMAINS = (
    "sensor",
    "binary_sensor",
    "number",
    "time",
    "select",
    "switch",
)

EXISTING_CONTROL_WRITE_POINTS = {
    11009: ("number", "inverter_input_limit", 1138),
    2618: ("switch", "grid", 1143),
    6505: ("number", "backup_soc", 1142),
    11010: ("number", "feed_in_power_limit", 1146),
}


class FakeAPI:
    """Record the exact wire write caused by one HA entity operation."""

    def __init__(self) -> None:
        self.writes: list[tuple[int, list[int | float | None]]] = []

    async def set_data(self, *, point, value):
        self.writes.append((point, list(value)))
        return True


class FakeCoordinator:
    """Provide all first-refresh values needed by the guessed user entities."""

    def __init__(self, model: str) -> None:
        self.api = FakeAPI()
        self.config_entry = SimpleNamespace(
            unique_id=SERIAL,
            data={
                "sn": SERIAL,
                "device_model": model,
                "fw_version": "capability-test",
            },
        )
        self.data = {
            str(capability.point): capability.sample_value
            for capability in GET_USER_CAPABILITIES
        }
        self.data.update(
            {point: f"PACK-{pack_id}" for pack_id, point in PACK_SERIAL_POINTS.items()}
        )
        # These readable counterparts predate the point-table additions, but a
        # bidirectional control needs them to display a useful initial value.
        self.data.update({"8646": 30, "8647": 0x0800, "2802": 100})
        self.data.update({"7101": 1, "7171": 1, "2618": 1001, "680": 1})
        self.last_update_success = True
        self.refreshes = 0
        self.request_refreshes = 0
        self.updated_data: list[dict[str, Any]] = []

    async def async_refresh(self) -> None:
        self.refreshes += 1

    async def async_request_refresh(self) -> None:
        self.request_refreshes += 1

    def async_set_updated_data(self, data) -> None:
        self.data = dict(data)
        self.updated_data.append(dict(data))


@dataclass(slots=True)
class ModelUserHarness:
    """Entities and observable side effects for one exact-model test."""

    model: str
    coordinator: FakeCoordinator = field(init=False)
    entities: dict[tuple[str, str], Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.coordinator = FakeCoordinator(self.model)

    async def set_up_platforms(self) -> None:
        entry = SimpleNamespace(
            data={"device_model": self.model},
            runtime_data=self.coordinator,
        )

        for domain in CAPABILITY_DOMAINS:
            module = _optional_integration_platform(domain)
            if module is None:
                continue

            added: list[Any] = []

            def async_add_entities(entities, *args, **kwargs) -> None:
                added.extend(entities)

            await module.async_setup_entry(None, entry, async_add_entities)
            for entity in added:
                unique_id = entity.unique_id
                key = (domain, unique_id)
                if key in self.entities:
                    raise AssertionError(f"duplicate entity registration: {key}")
                self.entities[key] = entity

    def entity_for_get(self, capability: GetUserCapability):
        return self.entities.get(
            (capability.domain, capability.unique_id(SERIAL)),
        )

    def entity_for_set(self, capability: SetUserCapability):
        assert capability.key is not None
        assert capability.entity_domain is not None
        return self.entities.get(
            (capability.entity_domain, f"{SERIAL}_{capability.key}")
        )


def _optional_integration_platform(domain: str) -> ModuleType | None:
    module_name = f"custom_components.indevolt.{domain}"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as err:
        if err.name != module_name:
            raise
        return None


def entity_state(entity: Any, domain: str) -> str:
    """Render a directly constructed entity as a user-visible HA state."""
    if domain == "binary_sensor":
        return "on" if entity.is_on else "off"
    if domain == "select":
        return entity.current_option or "unknown"

    value = entity.native_value
    if value is None:
        return "unknown"
    if domain == "time":
        return value.isoformat()
    return str(value)


def entity_unit(entity: Any) -> str | None:
    """Read static unit metadata without requiring an HA entity platform."""
    return getattr(entity.entity_description, "native_unit_of_measurement", None)


def entity_enabled_by_default(entity: Any) -> bool:
    return entity.entity_description.entity_registry_enabled_default


def expected_device_identifier(capability: GetUserCapability) -> tuple[str, str]:
    if capability.scope == "main":
        return DOMAIN, SERIAL

    pack_id = int(capability.scope.removeprefix("battery_"))
    return DOMAIN, f"battery_{pack_id}_PACK-{pack_id}"


async def operate_control(entity: Any, capability: SetUserCapability) -> None:
    """Perform the same entity operation Home Assistant exposes to a user."""
    if capability.exposure == "number":
        await entity.async_set_native_value(capability.user_value)
        return
    if capability.entity_domain == "select":
        await entity.async_select_option(capability.user_value)
        return
    if capability.exposure == "time":
        await entity.async_set_value(capability.user_value)
        return
    raise AssertionError(f"point {capability.point} is not a user control")


async def assert_get_user_capability(
    model: str,
    capability: GetUserCapability,
) -> None:
    """Assert one protocol value becomes the guessed user-visible HA entity."""
    harness = ModelUserHarness(model)
    await harness.set_up_platforms()
    entity = harness.entity_for_get(capability)

    assert entity is not None, (
        f"point {capability.point} should register {capability.domain}."
        f"{capability.key} for {model}"
    )
    assert entity.entity_description.name == capability.name
    assert entity_state(entity, capability.domain) == capability.expected_state
    assert entity_unit(entity) == capability.unit
    assert entity_enabled_by_default(entity) is capability.enabled_by_default
    assert expected_device_identifier(capability) in entity.device_info["identifiers"]

    if capability.scope.startswith("battery_"):
        assert entity.device_info["via_device"] == (DOMAIN, SERIAL)


async def assert_set_user_capability(
    model: str,
    capability: SetUserCapability,
) -> None:
    """Assert one guessed HA control emits its documented OpenData write."""
    assert capability.user_visible
    harness = ModelUserHarness(model)
    await harness.set_up_platforms()
    entity = harness.entity_for_set(capability)

    assert entity is not None, (
        f"point {capability.point} should be operable through "
        f"{capability.entity_domain}.{capability.key} for {model}"
    )
    assert entity.entity_description.name == capability.name
    assert entity_enabled_by_default(entity) is capability.enabled_by_default
    assert entity_state(entity, capability.entity_domain) == (
        capability.expected_initial_state
    )

    if capability.entity_domain == "number":
        assert entity.native_min_value == capability.minimum
        assert entity.native_max_value == capability.maximum
        assert entity.native_step == capability.step
        assert entity_unit(entity) == capability.unit
    elif capability.entity_domain == "select":
        assert tuple(entity.options) == capability.options

    await operate_control(entity, capability)

    assert harness.coordinator.api.writes == [
        (capability.point, [capability.wire_value])
    ]
    assert harness.coordinator.refreshes + harness.coordinator.request_refreshes == 1


async def assert_set_point_is_not_exposed_as_a_new_user_control(
    model: str,
    capability: SetUserCapability,
) -> None:
    """Assert one documented non-user write point adds no new HA control."""
    assert not capability.user_visible
    harness = ModelUserHarness(model)
    await harness.set_up_platforms()

    assert capability.name not in {
        entity.entity_description.name for entity in harness.entities.values()
    }

    for (domain, _unique_id), entity in harness.entities.items():
        description = entity.entity_description
        if domain == "number":
            value = description.native_min_value
            await description.set_fn(harness.coordinator.api, float(value or 0))
        elif domain == "select":
            await description.set_fn(harness.coordinator, 0)
        elif domain == "switch":
            await description.set_fn(harness.coordinator.api, True)

    written_points = {point for point, _value in harness.coordinator.api.writes}
    assert capability.point not in written_points

    if capability.exposure == "existing_control_transport":
        domain, key, existing_write_point = EXISTING_CONTROL_WRITE_POINTS[
            capability.point
        ]
        assert (domain, f"{SERIAL}_{key}") in harness.entities
        assert existing_write_point in written_points
