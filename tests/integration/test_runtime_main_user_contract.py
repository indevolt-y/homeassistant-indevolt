"""Protect local MAIN users from destructive runtime regressions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from custom_components.indevolt.const import DOMAIN

from ._support import (
    FakeDevice,
    add_entry,
    home_assistant_runtime,
    install_fake_devices,
    make_entry,
)

MAIN_CONTRACT_PATH = (
    Path(__file__).parents[1] / "fixtures" / "main_user_visible_contract.json"
)
ALLOWED_NON_DESTRUCTIVE_ENTITY_FIELDS = frozenset({"translation_key"})
ALLOWED_WORK_MODE_OPTION = "Custom Time Control Mode"
DESTRUCTIVE_CHANGE_RECORD_FIELDS = frozenset(
    {
        "scope",
        "affected_users",
        "observable_impact",
        "why_unavoidable",
        "migration_or_recovery",
        "rollback",
    }
)


def _jsonable(value: Any) -> Any:
    """Convert stable Home Assistant values to their JSON representation."""
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]

    raw_value = getattr(value, "value", value)
    if raw_value is not value:
        return _jsonable(raw_value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _device_key(device) -> str:
    """Return a deterministic key without using HA's generated device ID."""
    return "|".join(
        f"{domain}:{identifier}" for domain, identifier in sorted(device.identifiers)
    )


def _device_snapshot(hass, device) -> dict[str, Any]:
    """Return the stable, user-visible fields for one device."""
    registry = dr.async_get(hass)
    via_device = (
        registry.async_get(device.via_device_id) if device.via_device_id else None
    )

    return {
        "identifiers": sorted([list(identifier) for identifier in device.identifiers]),
        "name": device.name,
        "name_by_user": device.name_by_user,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "model_id": device.model_id,
        "serial_number": device.serial_number,
        "sw_version": device.sw_version,
        "hw_version": device.hw_version,
        "configuration_url": device.configuration_url,
        "entry_type": _jsonable(device.entry_type),
        "disabled_by": _jsonable(device.disabled_by),
        "area_id": device.area_id,
        "via_identifiers": (
            sorted([list(identifier) for identifier in via_device.identifiers])
            if via_device
            else None
        ),
    }


def _device_snapshots(hass, entry) -> dict[str, dict[str, Any]]:
    """Capture each device once instead of repeating it for every entity."""
    registry = dr.async_get(hass)
    devices = {
        _device_key(device): _device_snapshot(hass, device)
        for device in registry.devices.values()
        if entry.entry_id in device.config_entries
    }
    return dict(sorted(devices.items()))


def _entity_snapshot(hass, entry) -> dict[str, dict[str, Any]]:
    """Capture every stable registry and state field visible to an HA user."""
    registry = er.async_get(hass)
    entities: dict[str, dict[str, Any]] = {}

    for registry_entry in registry.entities.values():
        if (
            registry_entry.platform != DOMAIN
            or registry_entry.config_entry_id != entry.entry_id
        ):
            continue

        state = hass.states.get(registry_entry.entity_id)
        device = (
            dr.async_get(hass).async_get(registry_entry.device_id)
            if registry_entry.device_id
            else None
        )
        entities[registry_entry.unique_id] = {
            "entity_id": registry_entry.entity_id,
            "domain": registry_entry.domain,
            "original_name": registry_entry.original_name,
            "original_icon": registry_entry.original_icon,
            "original_device_class": _jsonable(registry_entry.original_device_class),
            "translation_key": registry_entry.translation_key,
            "has_entity_name": registry_entry.has_entity_name,
            "entity_category": _jsonable(registry_entry.entity_category),
            "disabled_by": _jsonable(registry_entry.disabled_by),
            "hidden_by": _jsonable(registry_entry.hidden_by),
            "capabilities": _jsonable(registry_entry.capabilities),
            "device": _device_key(device) if device else None,
            "state": state.state if state else None,
            "attributes": _jsonable(dict(state.attributes)) if state else None,
        }

    return dict(sorted(entities.items()))


def _state_snapshot(hass, entry) -> dict[str, str | None]:
    """Capture the state seen by a user for every existing entity."""
    registry = er.async_get(hass)
    states: dict[str, str | None] = {}
    for registry_entry in registry.entities.values():
        if (
            registry_entry.platform != DOMAIN
            or registry_entry.config_entry_id != entry.entry_id
        ):
            continue
        state = hass.states.get(registry_entry.entity_id)
        states[registry_entry.unique_id] = state.state if state else None
    return dict(sorted(states.items()))


def _runtime_snapshot(hass, entry, backend: FakeDevice) -> dict[str, Any]:
    """Capture the complete initial user contract for one config entry."""
    services = hass.services.async_services().get(DOMAIN, {})
    return {
        "config_entry": {
            "title": entry.title,
            "unique_id": entry.unique_id,
            "data": _jsonable(dict(entry.data)),
            "options": _jsonable(dict(entry.options)),
            "source": entry.source,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "state": _jsonable(entry.state),
            "pref_disable_new_entities": entry.pref_disable_new_entities,
            "pref_disable_polling": entry.pref_disable_polling,
        },
        "polling": {
            "batches": [list(batch) for batch in backend.fetches],
            "interval_seconds": entry.runtime_data.update_interval.total_seconds(),
        },
        "registered_actions": sorted(services),
        "devices": _device_snapshots(hass, entry),
        "entities": _entity_snapshot(hass, entry),
    }


def _load_main_contract() -> dict[str, Any]:
    return json.loads(MAIN_CONTRACT_PATH.read_text())


def _expand_route_contract(value: Any, scenario: dict[str, str]) -> Any:
    """Fill scenario-specific values into one frozen MAIN runtime route."""
    replacements = {
        "{model}": scenario["model"],
        "{serial}": scenario["serial"],
        "{host}": scenario["host"],
        "{firmware}": scenario["firmware"],
        "{model_slug}": slugify(scenario["model"]),
        "{serial_slug}": slugify(scenario["serial"]),
    }

    if isinstance(value, dict):
        return {
            _expand_route_contract(key, scenario): _expand_route_contract(
                item, scenario
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_expand_route_contract(item, scenario) for item in value]
    if isinstance(value, str):
        for marker, replacement in replacements.items():
            value = value.replace(marker, replacement)
    return value


def _scenario_contract(
    contract: dict[str, Any],
    scenario_name: str,
    section: str,
) -> tuple[dict[str, str], dict[str, Any]]:
    scenario = contract["scenarios"][scenario_name]
    route = contract["routes"][scenario["route"]][section]
    return scenario, _expand_route_contract(route, scenario)


def _contract_differences(
    actual: Any,
    expected: Any,
    path: str = "$",
) -> list[str]:
    """Return precise snapshot differences without hiding them in a giant dict."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        differences: list[str] = []
        for key in sorted(actual.keys() | expected.keys()):
            child_path = f"{path}.{key}"
            if key not in actual:
                differences.append(f"{child_path}: missing; MAIN={expected[key]!r}")
            elif key not in expected:
                differences.append(f"{child_path}: added={actual[key]!r}")
            else:
                differences.extend(
                    _contract_differences(actual[key], expected[key], child_path)
                )
        return differences
    if isinstance(actual, list) and isinstance(expected, list):
        if actual == expected:
            return []
        return [f"{path}: current={actual!r}; MAIN={expected!r}"]
    if actual != expected:
        return [f"{path}: current={actual!r}; MAIN={expected!r}"]
    return []


def _assert_main_contract(actual: Any, expected: Any) -> None:
    differences = _contract_differences(actual, expected)
    assert not differences, "\n".join(differences[:100])


def _main_owned_mapping(
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Keep every MAIN-owned key while leaving new point additions separate."""
    return {key: actual[key] for key in expected if key in actual}


def _main_initial_view(
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Select the destructive MAIN contract without rejecting approved additions."""
    view = dict(actual)
    view["entities"] = {
        unique_id: {
            field: value
            for field, value in entity.items()
            if field not in ALLOWED_NON_DESTRUCTIVE_ENTITY_FIELDS
        }
        for unique_id, entity in _main_owned_mapping(
            actual["entities"], expected["entities"]
        ).items()
    }
    for unique_id, entity in view["entities"].items():
        if not unique_id.endswith("_work_mode"):
            continue
        expected_entity = expected["entities"][unique_id]
        for field in ("attributes", "capabilities"):
            entity[field] = dict(entity[field])
            main_options = expected_entity[field].get("options")
            current_options = entity[field].get("options")
            if current_options == [*main_options, ALLOWED_WORK_MODE_OPTION]:
                entity[field]["options"] = main_options
    view["polling"] = dict(actual["polling"])
    main_batch_count = len(expected["polling"]["batches"])
    view["polling"]["batches"] = actual["polling"]["batches"][:main_batch_count]
    return view


def test_any_unavoidable_destructive_change_requires_a_complete_record() -> None:
    """A breaking exception cannot be approved with a vague one-line comment."""
    changes = _load_main_contract()["approved_destructive_changes"]
    for change in changes:
        assert set(change) == DESTRUCTIVE_CHANGE_RECORD_FIELDS
        assert all(
            isinstance(change[field], str) and change[field].strip()
            for field in DESTRUCTIVE_CHANGE_RECORD_FIELDS
        )


def test_each_non_destructive_exception_is_narrow_and_explained() -> None:
    """Compatibility exclusions must remain explicit and reviewable."""
    allowed = _load_main_contract()["allowed_non_destructive_changes"]

    assert set(allowed) == {
        "entity_translation_key",
        "work_mode_custom_time_option",
    }
    translation = allowed["entity_translation_key"]
    assert set(translation) == {"reason", "separate_test"}
    assert translation["reason"].strip()
    assert (Path(__file__).parents[2] / translation["separate_test"]).is_file()
    work_mode = allowed["work_mode_custom_time_option"]
    assert set(work_mode) == {"reason", "separate_test"}
    assert work_mode["reason"].strip()
    assert (Path(__file__).parents[2] / work_mode["separate_test"]).is_file()


@pytest.mark.parametrize("scenario_name", ["bk", "default", "fallback"])
@pytest.mark.asyncio
async def test_complete_old_device_matches_main_user_visible_contract(
    monkeypatch,
    tmp_path,
    scenario_name,
) -> None:
    """Every MAIN-owned entity must remain safe for existing users."""
    contract = _load_main_contract()
    scenario, expected = _scenario_contract(contract, scenario_name, "complete")
    backend = FakeDevice(dict(expected["initial_response"]))
    install_fake_devices(monkeypatch, {scenario["host"]: backend})
    entry = make_entry(
        host=scenario["host"],
        serial=scenario["serial"],
        model=scenario["model"],
        firmware=scenario["firmware"],
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        assert entry.state is ConfigEntryState.LOADED
        actual = {"initial": _runtime_snapshot(hass, entry, backend)}

        backend.data = dict(expected["updated_response"])
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        actual["updated_states"] = _state_snapshot(hass, entry)

        backend.fetch_error = RuntimeError("MAIN offline fixture")
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        actual["failed_states"] = _state_snapshot(hass, entry)

        backend.fetch_error = None
        backend.data = {}
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        actual["missing_states"] = _state_snapshot(hass, entry)

        expected_contract = {
            "initial": _main_initial_view(expected["initial"], expected["initial"]),
            "updated_states": expected["updated_states"],
            "failed_states": expected["failed_states"],
            "missing_states": expected["missing_states"],
        }
        _assert_main_contract(
            {
                "initial": _main_initial_view(
                    actual["initial"], expected_contract["initial"]
                ),
                **{
                    phase: _main_owned_mapping(actual[phase], expected_contract[phase])
                    for phase in (
                        "updated_states",
                        "failed_states",
                        "missing_states",
                    )
                },
            },
            expected_contract,
        )


@pytest.mark.parametrize(
    ("scenario_name", "response_case"),
    [
        ("bk", "empty"),
        ("bk", "null"),
        ("default", "empty"),
        ("default", "null"),
        ("fallback", "empty"),
        ("fallback", "null"),
    ],
)
@pytest.mark.asyncio
async def test_incomplete_first_refresh_matches_main_entity_creation_contract(
    monkeypatch,
    tmp_path,
    scenario_name,
    response_case,
) -> None:
    """Missing and null first responses retain MAIN's exact entity behavior."""
    contract = _load_main_contract()
    scenario, first_refresh = _scenario_contract(
        contract,
        scenario_name,
        "first_refresh",
    )
    expected = first_refresh[response_case]
    backend = FakeDevice(dict(expected["response"]))
    install_fake_devices(monkeypatch, {scenario["host"]: backend})
    entry = make_entry(
        host=scenario["host"],
        serial=scenario["serial"],
        model=scenario["model"],
        firmware=scenario["firmware"],
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        assert entry.state is ConfigEntryState.LOADED
        actual_states = _state_snapshot(hass, entry)
        _assert_main_contract(
            _main_owned_mapping(actual_states, expected["states"]),
            expected["states"],
        )
