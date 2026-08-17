"""Home Assistant behavior contracts for the newly documented OpenData points."""

from __future__ import annotations

import asyncio
from datetime import time

import pytest
import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryDisabler

from custom_components.indevolt.const import DOMAIN
from tests.models._opendata_point_additions import (
    BASELINE_DEFAULT_POINT_BATCHES,
    DEFAULT_CAPABILITY_POINT_BATCHES,
    REMAINING_DEFAULT_USER_READ_POINTS,
)
from tests.models._opendata_user_testing import PACK_SERIAL_POINTS
from tests.models.opendata_capabilities import (
    BK_GET_USER_CAPABILITIES,
    GET_USER_CAPABILITIES,
    SET_USER_CAPABILITIES,
    GetUserCapability,
    SetUserCapability,
)

from ._support import (
    DEFAULT_DATA,
    FakeDevice,
    add_entry,
    device_for_serial,
    entry_entities,
    home_assistant_runtime,
    install_fake_devices,
    make_entry,
    state_for_unique_id,
)

HOST = "192.0.2.190"
SERIAL = "HA-POINT-CONTRACT-SN"
MODEL = "SolidFlex/PowerFlex2000"


def _complete_backend_data() -> dict[str, object]:
    """Return all values needed to exercise the proposed HA entities."""
    data: dict[str, object] = dict(DEFAULT_DATA)
    data.update(
        {
            str(capability.point): capability.sample_value
            for capability in GET_USER_CAPABILITIES
        }
    )
    data.update(
        {point: f"PACK-{pack_id}" for pack_id, point in PACK_SERIAL_POINTS.items()}
    )
    data.update({"8646": 30, "8647": 0x0800, "2802": 100})
    return data


def _get_capability(point: int) -> GetUserCapability:
    return next(item for item in GET_USER_CAPABILITIES if item.point == point)


def _set_capability(point: int) -> SetUserCapability:
    return next(
        item
        for item in SET_USER_CAPABILITIES
        if item.point == point and item.user_visible
    )


def _get_unique_id(point: int, serial: str = SERIAL) -> str:
    return _get_capability(point).unique_id(serial)


def _set_unique_id(point: int, serial: str = SERIAL) -> str:
    capability = _set_capability(point)
    assert capability.key is not None
    return f"{serial}_{capability.key}"


async def _refresh(hass, entry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_ha_01_missing_values_distinguish_unknown_from_unavailable(
    monkeypatch,
    tmp_path,
) -> None:
    """One missing value is unknown; a failed device refresh is unavailable."""
    backend = FakeDevice(_complete_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        unique_ids = (
            _get_unique_id(2278),
            _get_unique_id(64100),
            _set_unique_id(8646),
        )
        original_entity_ids = {
            unique_id: entry_entities(hass, entry)[unique_id].entity_id
            for unique_id in unique_ids
        }

        for point in ("2278", "64100", "8646"):
            backend.data[point] = None
        await _refresh(hass, entry)
        assert {
            unique_id: state_for_unique_id(hass, entry, unique_id).state
            for unique_id in unique_ids
        } == {unique_id: STATE_UNKNOWN for unique_id in unique_ids}

        for point in ("2278", "64100", "8646"):
            backend.data.pop(point)
        await _refresh(hass, entry)
        assert {
            unique_id: state_for_unique_id(hass, entry, unique_id).state
            for unique_id in unique_ids
        } == {unique_id: STATE_UNKNOWN for unique_id in unique_ids}

        backend.fetch_error = TimeoutError("device is offline")
        await _refresh(hass, entry)
        assert {
            unique_id: state_for_unique_id(hass, entry, unique_id).state
            for unique_id in unique_ids
        } == {unique_id: STATE_UNAVAILABLE for unique_id in unique_ids}

        backend.fetch_error = None
        backend.data.update({"2278": 0, "64100": 0, "8646": 0})
        await _refresh(hass, entry)
        assert state_for_unique_id(hass, entry, unique_ids[0]).state == "0"
        assert state_for_unique_id(hass, entry, unique_ids[1]).state == "off"
        assert state_for_unique_id(hass, entry, unique_ids[2]).state == "0"
        assert {
            unique_id: entry_entities(hass, entry)[unique_id].entity_id
            for unique_id in unique_ids
        } == original_entity_ids


@pytest.mark.asyncio
async def test_ha_02_raw_values_are_interpreted_as_ha_states(
    monkeypatch,
    tmp_path,
) -> None:
    """Signs, bounds, scaling, enums, booleans, and times reach HA intact."""
    data = _complete_backend_data()
    data.update(
        {
            "2275": -321,
            "9405": 0,
            "1505": 2500,
            "35001": 0,
            "9079": 99,
            "64100": 0,
        }
    )
    backend = FakeDevice(data)
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        expected = {
            _get_unique_id(2275): "-321",
            _get_unique_id(9405): "0",
            _get_unique_id(1505): "2.5",
            _get_unique_id(35001): "00:00:00",
            _get_unique_id(9079): STATE_UNKNOWN,
            _get_unique_id(64100): "off",
        }
        assert {
            unique_id: state_for_unique_id(hass, entry, unique_id).state
            for unique_id in expected
        } == expected

        backend.data.update(
            {
                "9405": 100,
                "35001": 0x173B,
                "9079": 2,
                "64100": 1,
            }
        )
        await _refresh(hass, entry)
        assert state_for_unique_id(hass, entry, _get_unique_id(9405)).state == "100"
        assert (
            state_for_unique_id(hass, entry, _get_unique_id(35001)).state == "23:59:00"
        )
        assert (
            state_for_unique_id(hass, entry, _get_unique_id(9079)).state
            == "discharging"
        )
        assert state_for_unique_id(hass, entry, _get_unique_id(64100)).state == "on"


@pytest.mark.asyncio
async def test_ha_03_controls_validate_input_and_report_write_failures(
    monkeypatch,
    tmp_path,
) -> None:
    """Invalid input never writes, and device rejection is not false success."""
    backend = FakeDevice(_complete_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)
        interval = entities[_set_unique_id(8646)].entity_id
        forced_power = entities[_set_unique_id(2802)].entity_id
        light_mode = entities[_set_unique_id(35005)].entity_id
        sleep_start = entities[_set_unique_id(35001)].entity_id

        for value in (-1, 30.5, 61):
            with pytest.raises(ServiceValidationError):
                await hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": interval, "value": value},
                    blocking=True,
                )
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": forced_power, "value": 100.5},
                blocking=True,
            )
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "select",
                "select_option",
                {"entity_id": light_mode, "option": "not-a-protocol-option"},
                blocking=True,
            )
        with pytest.raises((ServiceValidationError, vol.Invalid)):
            await hass.services.async_call(
                "time",
                "set_value",
                {"entity_id": sleep_start, "time": "25:00:00"},
                blocking=True,
            )
        assert backend.writes == []

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": interval, "value": 30},
            blocking=True,
        )
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": forced_power, "value": 100},
            blocking=True,
        )
        assert backend.writes == [(8646, [30]), (2802, [100])]
        backend.writes.clear()

        backend.write_result = False
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": interval, "value": 30},
                blocking=True,
            )

        backend.write_result = True
        backend.write_error = TimeoutError("write timed out")
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                "time",
                "set_value",
                {"entity_id": sleep_start, "time": time(18, 30)},
                blocking=True,
            )

        backend.write_error = ConnectionError("connection lost")
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                "select",
                "select_option",
                {"entity_id": light_mode, "option": "on"},
                blocking=True,
            )
        assert state_for_unique_id(hass, entry, _set_unique_id(8646)).state == "30"


@pytest.mark.asyncio
async def test_ha_03_simulated_load_controls_use_uint16_boundaries(
    monkeypatch,
    tmp_path,
) -> None:
    """Representative slots use whole watts across the documented uint16 range."""
    backend = FakeDevice(_complete_backend_data())
    write_to_read = {12197: 26000, 12220: 26023, 12244: 26047}

    async def remember_values(point, value) -> None:
        if point in write_to_read:
            backend.data[str(write_to_read[point])] = value[0]

    backend.before_write = remember_values
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        registry = er.async_get(hass)
        unique_ids = {point: _set_unique_id(point) for point in (12197, 12220, 12244)}

        for unique_id in unique_ids.values():
            registry_entry = entry_entities(hass, entry)[unique_id]
            assert registry_entry.disabled_by is RegistryEntryDisabler.INTEGRATION
            registry.async_update_entity(registry_entry.entity_id, disabled_by=None)

        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        entities = entry_entities(hass, entry)

        requested_values = {12197: 0, 12220: 65_535, 12244: 456}
        for point, value in requested_values.items():
            state = hass.states.get(entities[unique_ids[point]].entity_id)
            assert state is not None
            assert state.attributes["min"] == 0
            assert state.attributes["max"] == 65_535
            assert state.attributes["step"] == 1
            await hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": state.entity_id, "value": value},
                blocking=True,
            )

        assert backend.writes == [
            (12197, [0]),
            (12220, [65_535]),
            (12244, [456]),
        ]
        assert {
            point: state_for_unique_id(hass, entry, unique_id).state
            for point, unique_id in unique_ids.items()
        } == {12197: "0", 12220: "65535", 12244: "456"}

        for point, value in ((12197, -1), (12220, 65_536), (12244, 456.5)):
            with pytest.raises(ServiceValidationError):
                await hass.services.async_call(
                    "number",
                    "set_value",
                    {
                        "entity_id": entities[unique_ids[point]].entity_id,
                        "value": value,
                    },
                    blocking=True,
                )
        assert len(backend.writes) == 3

        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert {
            point: state_for_unique_id(hass, entry, unique_id).state
            for point, unique_id in unique_ids.items()
        } == {12197: "0", 12220: "65535", 12244: "456"}


@pytest.mark.asyncio
async def test_ha_04_refresh_and_reload_keep_entity_identity(
    monkeypatch,
    tmp_path,
) -> None:
    """Runtime updates and reloads change values without replacing entities."""
    backend = FakeDevice(_complete_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        tracked_unique_ids = {
            _get_unique_id(2278),
            _get_unique_id(64100),
            _get_unique_id(11039),
            _get_unique_id(35002),
            _get_unique_id(26000),
        }
        original = {
            unique_id: entry_entities(hass, entry)[unique_id].entity_id
            for unique_id in tracked_unique_ids
        }

        load_slot = entry_entities(hass, entry)[_get_unique_id(26000)]
        er.async_get(hass).async_update_entity(load_slot.entity_id, disabled_by=None)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.runtime_data
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        backend.data.update(
            {
                "2278": 333,
                "64100": 0,
                "11039": 1,
                "35002": 0x173B,
                "26000": 777,
            }
        )
        await _refresh(hass, entry)
        assert state_for_unique_id(hass, entry, _get_unique_id(2278)).state == "333"
        assert state_for_unique_id(hass, entry, _get_unique_id(64100)).state == "off"
        assert (
            state_for_unique_id(hass, entry, _get_unique_id(11039)).state
            == "microinverter_mode"
        )
        assert (
            state_for_unique_id(hass, entry, _get_unique_id(35002)).state == "23:59:00"
        )
        assert state_for_unique_id(hass, entry, _get_unique_id(26000)).state == "777"
        assert {
            unique_id: entry_entities(hass, entry)[unique_id].entity_id
            for unique_id in tracked_unique_ids
        } == original


@pytest.mark.asyncio
async def test_ha_05_user_registry_choices_survive_restart(
    monkeypatch,
    tmp_path,
) -> None:
    """Rename, disable, enable, and paired read/write identity survive restart."""
    backend = FakeDevice(_complete_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)
    sensor_unique_id = _get_unique_id(2278)
    binary_unique_id = _get_unique_id(64100)
    load_unique_id = _set_unique_id(12197)

    async with home_assistant_runtime(tmp_path, writable_storage=True) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)
        registry = er.async_get(hass)
        renamed = registry.async_update_entity(
            entities[sensor_unique_id].entity_id,
            new_entity_id="sensor.user_named_total_ac_power",
            name="User named total AC power",
        )
        disabled = registry.async_update_entity(
            entities[binary_unique_id].entity_id,
            disabled_by=RegistryEntryDisabler.USER,
        )
        enabled = registry.async_update_entity(
            entities[load_unique_id].entity_id,
            disabled_by=None,
        )
        await hass.async_block_till_done()
        original_entry_id = entry.entry_id
        original_registry_ids = {
            unique_id: entities[unique_id].id
            for unique_id in (sensor_unique_id, binary_unique_id, load_unique_id)
        }
        assert renamed.entity_id == "sensor.user_named_total_ac_power"
        assert disabled.disabled_by is RegistryEntryDisabler.USER
        assert enabled.disabled_by is None

    backend.data.update({"2278": 444, "64100": 0, "26000": 345})

    async with home_assistant_runtime(tmp_path, restore=True) as hass:
        restored = hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, SERIAL)
        assert restored is not None
        assert restored.entry_id == original_entry_id
        entities = entry_entities(hass, restored)
        assert {
            unique_id: entities[unique_id].id for unique_id in original_registry_ids
        } == original_registry_ids
        assert entities[sensor_unique_id].entity_id == (
            "sensor.user_named_total_ac_power"
        )
        assert entities[sensor_unique_id].name == "User named total AC power"
        assert entities[binary_unique_id].disabled_by is RegistryEntryDisabler.USER
        assert entities[load_unique_id].disabled_by is None
        assert hass.states.get(entities[sensor_unique_id].entity_id).state == "444"
        assert hass.states.get(entities[binary_unique_id].entity_id) is None
        assert hass.states.get(entities[load_unique_id].entity_id).state == "345"

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entities[load_unique_id].entity_id, "value": 456},
            blocking=True,
        )
        assert backend.writes == [(12197, [456.0])]
        assert len(entities) == len(set(entities))


@pytest.mark.asyncio
async def test_ha_06_model_route_and_returned_values_define_support(
    monkeypatch,
    tmp_path,
) -> None:
    """A version string cannot invent support; route and returned point still matter."""
    sf_data = dict(DEFAULT_DATA) | {"1127": 15}
    fallback_data = dict(DEFAULT_DATA) | {"2278": 321}
    bk_data = {
        "6001": 1001,
        **{
            str(capability.point): capability.sample_value
            for capability in BK_GET_USER_CAPABILITIES
        },
        "2278": 999,
    }
    devices = {
        "192.0.2.191": FakeDevice(sf_data),
        "192.0.2.192": FakeDevice(fallback_data),
        "192.0.2.193": FakeDevice(bk_data),
    }
    install_fake_devices(monkeypatch, devices)
    sf_entry = make_entry(
        host="192.0.2.191",
        serial="SUPPORT-SF-SN",
        model=MODEL,
        firmware="new-looking-version",
    )
    fallback_entry = make_entry(
        host="192.0.2.192",
        serial="SUPPORT-FALLBACK-SN",
        model="FutureModel",
        firmware="old-looking-version",
    )
    bk_entry = make_entry(
        host="192.0.2.193",
        serial="SUPPORT-BK-SN",
        model="BK1600/BK1600Ultra",
        firmware="new-looking-version",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        for entry in (sf_entry, fallback_entry, bk_entry):
            await add_entry(hass, entry)

        sf_ids = set(entry_entities(hass, sf_entry))
        assert _get_unique_id(1127, "SUPPORT-SF-SN") in sf_ids
        assert _get_unique_id(2278, "SUPPORT-SF-SN") not in sf_ids

        fallback_ids = set(entry_entities(hass, fallback_entry))
        assert _get_unique_id(2278, "SUPPORT-FALLBACK-SN") in fallback_ids

        bk_ids = set(entry_entities(hass, bk_entry))
        assert _get_unique_id(2278, "SUPPORT-BK-SN") not in bk_ids
        bk_bms = next(item for item in BK_GET_USER_CAPABILITIES if item.point == 1107)
        assert bk_bms.unique_id("SUPPORT-BK-SN") in bk_ids


@pytest.mark.asyncio
async def test_ha_07_new_battery_points_share_the_existing_pack_lifecycle(
    monkeypatch,
    tmp_path,
) -> None:
    """New values follow the existing pack entity without a second device."""
    backend = FakeDevice(_complete_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)
    cycle_unique_id = _get_unique_id(9019)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        original_entity = entry_entities(hass, entry)[cycle_unique_id]
        existing_soc = entry_entities(hass, entry)[f"{SERIAL}_battery_1_9016"]
        original_device = device_for_serial(hass, "battery_1_PACK-1")
        assert original_device is not None
        assert original_entity.device_id == original_device.id
        assert original_entity.device_id == existing_soc.device_id

        backend.data[PACK_SERIAL_POINTS[1]] = ""
        await _refresh(hass, entry)
        assert state_for_unique_id(hass, entry, cycle_unique_id).state == (
            STATE_UNAVAILABLE
        )

        backend.data[PACK_SERIAL_POINTS[1]] = "PACK-1"
        await _refresh(hass, entry)
        assert entry_entities(hass, entry)[cycle_unique_id].id == original_entity.id
        assert state_for_unique_id(hass, entry, cycle_unique_id).state != (
            STATE_UNAVAILABLE
        )

        backend.data[PACK_SERIAL_POINTS[1]] = "PACK-REPLACED"
        await _refresh(hass, entry)
        entities = entry_entities(hass, entry)
        assert entities[cycle_unique_id].id == original_entity.id
        assert entities[cycle_unique_id].device_id == (
            entities[f"{SERIAL}_battery_1_9016"].device_id
        )
        assert device_for_serial(hass, "battery_1_PACK-REPLACED") is None


@pytest.mark.asyncio
async def test_ha_08_expanded_polling_is_atomic_serialized_and_recovers(
    monkeypatch,
    tmp_path,
) -> None:
    """A failed later batch publishes no partial snapshot and recovery is clean."""
    backend = FakeDevice(_complete_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)
    expected_batches = (
        BASELINE_DEFAULT_POINT_BATCHES
        + DEFAULT_CAPABILITY_POINT_BATCHES
        + (REMAINING_DEFAULT_USER_READ_POINTS,)
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        coordinator = entry.runtime_data
        original_data = dict(coordinator.data)
        backend.data["2278"] = 777
        backend.fetches.clear()
        failure_raised = False

        async def fail_one_later_batch(keys: list[int]) -> None:
            nonlocal failure_raised
            if 11036 in keys and not failure_raised:
                failure_raised = True
                raise RuntimeError("one expanded batch failed")

        backend.before_fetch = fail_one_later_batch
        await _refresh(hass, entry)
        assert failure_raised is True
        assert coordinator.last_update_success is True
        assert coordinator.data != original_data
        assert "2278" not in coordinator.data
        assert state_for_unique_id(hass, entry, _get_unique_id(2278)).state == (
            STATE_UNKNOWN
        )
        assert state_for_unique_id(hass, entry, f"{SERIAL}_142").state == "2048"

        backend.fetches.clear()
        active_fetches = 0
        maximum_active_fetches = 0

        async def observe_fetch(_keys: list[int]) -> None:
            nonlocal active_fetches, maximum_active_fetches
            active_fetches += 1
            maximum_active_fetches = max(maximum_active_fetches, active_fetches)
            await asyncio.sleep(0)
            active_fetches -= 1

        backend.before_fetch = observe_fetch
        await asyncio.gather(coordinator.async_refresh(), coordinator.async_refresh())
        await hass.async_block_till_done()

        assert backend.fetches == [list(batch) for batch in expected_batches] * 2
        assert all(len(batch) <= 8 for batch in backend.fetches)
        assert maximum_active_fetches == 1
        assert coordinator.last_update_success is True
        assert state_for_unique_id(hass, entry, _get_unique_id(2278)).state == "777"


@pytest.mark.parametrize(
    ("model", "host", "serial", "added_point", "existing_unique_id"),
    [
        (
            "BK1600/BK1600Ultra",
            "192.0.2.194",
            "OLD-BK-SN",
            1107,
            "OLD-BK-SN_6001",
        ),
        (
            "SolidFlex/PowerFlex2000",
            "192.0.2.195",
            "OLD-SF-SN",
            2278,
            "OLD-SF-SN_142",
        ),
        (
            "FutureModel",
            "192.0.2.196",
            "OLD-FALLBACK-SN",
            2278,
            "OLD-FALLBACK-SN_142",
        ),
    ],
)
@pytest.mark.asyncio
async def test_added_batch_failure_does_not_block_existing_device_setup(
    monkeypatch,
    tmp_path,
    model: str,
    host: str,
    serial: str,
    added_point: int,
    existing_unique_id: str,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))

    async def reject_added_batch(keys: list[int]) -> None:
        if added_point in keys:
            raise RuntimeError("old firmware rejects an added batch")

    backend.before_fetch = reject_added_batch
    install_fake_devices(monkeypatch, {host: backend})
    entry = make_entry(host=host, serial=serial, model=model, firmware="old-firmware")

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        assert entry.state is ConfigEntryState.LOADED
        existing_state = state_for_unique_id(hass, entry, existing_unique_id)
        assert existing_state is not None
        assert existing_state.state != STATE_UNAVAILABLE


@pytest.mark.asyncio
async def test_ha_09_energy_metadata_matches_long_term_statistics_semantics(
    monkeypatch,
    tmp_path,
) -> None:
    """Lifetime and resetting daily energy totals use distinct HA semantics."""
    backend = FakeDevice(_complete_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)
    lifetime_points = (11007, 9284)
    daily_points = (11036, 9285, 11035, 11037)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        for point in lifetime_points:
            state = state_for_unique_id(hass, entry, _get_unique_id(point))
            assert state.attributes["device_class"] == SensorDeviceClass.ENERGY
            assert state.attributes["state_class"] == SensorStateClass.TOTAL
            assert state.attributes["unit_of_measurement"] in {"Wh", "kWh"}

        cumulative_production = state_for_unique_id(hass, entry, _get_unique_id(1505))
        assert (
            cumulative_production.attributes["device_class"] == SensorDeviceClass.ENERGY
        )
        assert cumulative_production.attributes["state_class"] == (
            SensorStateClass.TOTAL_INCREASING
        )
        assert cumulative_production.attributes["unit_of_measurement"] == "kWh"

        for point in daily_points:
            state = state_for_unique_id(hass, entry, _get_unique_id(point))
            assert state.attributes["device_class"] == SensorDeviceClass.ENERGY
            assert state.attributes["state_class"] == (
                SensorStateClass.TOTAL_INCREASING
            )
            assert state.attributes["unit_of_measurement"] == "Wh"


@pytest.mark.asyncio
async def test_ha_10_defaults_limit_noise_without_hiding_capabilities(
    monkeypatch,
    tmp_path,
) -> None:
    """High-volume entities default off but remain explicit and user-enableable."""
    backend = FakeDevice(_complete_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)
        new_unique_ids = {
            capability.unique_id(SERIAL) for capability in GET_USER_CAPABILITIES
        } | {
            _set_unique_id(capability.point)
            for capability in SET_USER_CAPABILITIES
            if capability.user_visible
        }
        disabled_unique_ids = {
            capability.unique_id(SERIAL)
            for capability in GET_USER_CAPABILITIES
            if not capability.enabled_by_default
        } | {
            _set_unique_id(capability.point)
            for capability in SET_USER_CAPABILITIES
            if capability.user_visible and not capability.enabled_by_default
        }

        assert new_unique_ids <= set(entities)
        assert len(new_unique_ids) == len(
            {entities[item].id for item in new_unique_ids}
        )
        for unique_id in new_unique_ids:
            entity = entities[unique_id]
            assert entity.hidden_by is None
            if unique_id in disabled_unique_ids:
                assert entity.disabled_by is RegistryEntryDisabler.INTEGRATION
                assert hass.states.get(entity.entity_id) is None
            else:
                assert entity.disabled_by is None

        uplink = entities[_get_unique_id(9267)]
        er.async_get(hass).async_update_entity(uplink.entity_id, disabled_by=None)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.runtime_data
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        enabled_uplink = entry_entities(hass, entry)[_get_unique_id(9267)]
        assert enabled_uplink.id == uplink.id
        assert enabled_uplink.disabled_by is None
        assert hass.states.get(enabled_uplink.entity_id) is not None
