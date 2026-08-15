"""Real Home Assistant user journey for the guessed OpenData abilities."""

from __future__ import annotations

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryDisabler

from custom_components.indevolt.const import DOMAIN
from tests.models._opendata_point_additions import (
    BK_NON_USER_READ_POINTS,
    DEFAULT_NON_USER_READ_POINTS,
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

HOST = "192.0.2.180"
SERIAL = "CAPABILITY-RUNTIME-SN"
MODEL = "SolidFlex/PowerFlex2000"
BK_HOST = "192.0.2.181"
BK_SERIAL = "BK-CAPABILITY-RUNTIME-SN"
BK_MODEL = "BK1600/BK1600Ultra"
MODBUS_VERSION_POINT = "1127"
HIDDEN_WRITE_SAMPLES = {
    "15203": 0,
    "15204": 0,
    "18000": 1,
    "18001": 0,
}
BASELINE_UNIQUE_IDS = {
    f"{SERIAL}_work_mode",
    f"{SERIAL}_state_setting",
    f"{SERIAL}_load_setting",
    f"{SERIAL}_light",
    f"{SERIAL}_grid",
    f"{SERIAL}_bypass",
    f"{SERIAL}_backup_soc",
    f"{SERIAL}_inverter_input_limit",
    f"{SERIAL}_max_output_power",
    f"{SERIAL}_feed_in_power_limit",
    f"{SERIAL}_power_setting",
    f"{SERIAL}_soc_setting",
    f"{SERIAL}_1118",
    f"{SERIAL}_142",
    f"{SERIAL}_battery_1_9016",
}
BK_ALWAYS_PRESENT_UNIQUE_IDS = {
    f"{BK_SERIAL}_6001",
    f"{BK_SERIAL}_power_setting",
    f"{BK_SERIAL}_soc_setting",
    f"{BK_SERIAL}_state_setting",
}


def capability_backend_data() -> dict[str, object]:
    """Return one complete first refresh as a device owner would receive it."""
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
    # These SetData-only inputs are present deliberately so the runtime test can
    # prove that production setup never polls them as user capabilities.
    data.update(HIDDEN_WRITE_SAMPLES)
    return data


def bk_capability_backend_data() -> dict[str, object]:
    """Return all guessed BK values that should become visible in HA."""
    return {
        "6001": 1001,
        **{
            str(capability.point): capability.sample_value
            for capability in BK_GET_USER_CAPABILITIES
        },
    }


def set_unique_id(capability: SetUserCapability) -> str:
    assert capability.key is not None
    return f"{SERIAL}_{capability.key}"


def expected_unique_ids() -> set[str]:
    """Include old entities, new read entities, and genuinely new controls."""
    visible_sets = {
        set_unique_id(capability)
        for capability in SET_USER_CAPABILITIES
        if capability.user_visible
    }
    return (
        BASELINE_UNIQUE_IDS
        | {capability.unique_id(SERIAL) for capability in GET_USER_CAPABILITIES}
        | visible_sets
    )


def assert_get_state(
    hass,
    entry,
    capability: GetUserCapability,
    *,
    serial: str = SERIAL,
) -> None:
    unique_id = capability.unique_id(serial)
    registry_entry = entry_entities(hass, entry)[unique_id]

    assert registry_entry.domain == capability.domain
    assert registry_entry.translation_key == capability.translation_key
    assert registry_entry.entity_category == capability.entity_category
    assert registry_entry.has_entity_name is True
    if capability.enabled_by_default:
        assert registry_entry.disabled_by is None
        state = state_for_unique_id(hass, entry, unique_id)
        assert state is not None
        assert state.state == capability.expected_state
        assert state.attributes.get("unit_of_measurement") == capability.unit
        assert state.attributes.get("device_class") == capability.device_class
        assert state.attributes.get("state_class") == capability.state_class
        if capability.options:
            assert tuple(state.attributes["options"]) == capability.options
        if capability.icon:
            assert state.attributes["icon"] == capability.icon
        assert state.attributes["friendly_name"].endswith(capability.name)
    else:
        assert registry_entry.disabled_by is RegistryEntryDisabler.INTEGRATION
        assert state_for_unique_id(hass, entry, unique_id) is None

    if capability.scope == "main":
        expected_device = device_for_serial(hass, serial)
    else:
        pack_id = capability.scope.removeprefix("battery_")
        expected_device = device_for_serial(hass, f"battery_{pack_id}_PACK-{pack_id}")
    assert expected_device is not None
    assert registry_entry.device_id == expected_device.id


def assert_set_entity(hass, entry, capability: SetUserCapability) -> None:
    unique_id = set_unique_id(capability)
    registry_entry = entry_entities(hass, entry)[unique_id]

    assert registry_entry.domain == capability.entity_domain
    assert registry_entry.translation_key == capability.translation_key
    assert registry_entry.entity_category == capability.entity_category
    assert registry_entry.has_entity_name is True
    device = device_for_serial(hass, SERIAL)
    assert device is not None
    assert registry_entry.device_id == device.id
    if capability.enabled_by_default:
        assert registry_entry.disabled_by is None
        state = state_for_unique_id(hass, entry, unique_id)
        assert state is not None
        assert state.state == capability.expected_initial_state
        if capability.entity_domain == "number":
            assert state.attributes["min"] == capability.minimum
            assert state.attributes["max"] == capability.maximum
            assert state.attributes["step"] == capability.step
            assert state.attributes.get("unit_of_measurement") == capability.unit
            assert state.attributes.get("device_class") == capability.device_class
            assert state.attributes["mode"] == capability.mode
        elif capability.entity_domain == "select":
            assert tuple(state.attributes["options"]) == capability.options
        if capability.icon:
            assert state.attributes["icon"] == capability.icon
    else:
        assert registry_entry.disabled_by is RegistryEntryDisabler.INTEGRATION
        assert state_for_unique_id(hass, entry, unique_id) is None


@pytest.mark.asyncio
async def test_modbus_version_does_not_unlock_unreturned_capabilities(
    monkeypatch,
    tmp_path,
) -> None:
    """Point 1127 describes Modbus; it is not a global capability switch."""
    backend_data = dict(DEFAULT_DATA)
    backend_data[MODBUS_VERSION_POINT] = 15
    backend = FakeDevice(backend_data)
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        version_capability = next(
            capability
            for capability in GET_USER_CAPABILITIES
            if str(capability.point) == MODBUS_VERSION_POINT
        )
        assert set(entry_entities(hass, entry)) == BASELINE_UNIQUE_IDS | {
            version_capability.unique_id(SERIAL)
        }
        assert_get_state(hass, entry, version_capability)
        work_mode = state_for_unique_id(hass, entry, f"{SERIAL}_work_mode")
        assert work_mode is not None
        assert work_mode.state == "Self-Consumed Prioritized"
        assert tuple(work_mode.attributes["options"]) == (
            "Self-Consumed Prioritized",
            "Real-Time Control",
            "Charge/Discharge Schedule",
        )


@pytest.mark.asyncio
async def test_returned_new_points_do_not_depend_on_modbus_version(
    monkeypatch,
    tmp_path,
) -> None:
    """Each returned point is usable even when point 1127 is absent."""
    backend_data = capability_backend_data()
    backend_data.pop(MODBUS_VERSION_POINT)
    backend = FakeDevice(backend_data)
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        version_capability = next(
            capability
            for capability in GET_USER_CAPABILITIES
            if str(capability.point) == MODBUS_VERSION_POINT
        )
        assert set(entry_entities(hass, entry)) == expected_unique_ids() - {
            version_capability.unique_id(SERIAL)
        }


@pytest.mark.asyncio
async def test_setdata_only_inputs_are_not_polled_as_user_capabilities(
    monkeypatch,
    tmp_path,
) -> None:
    """SetData-only inputs never enter the production read path."""
    backend = FakeDevice(capability_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        requested_points = {str(point) for batch in backend.fetches for point in batch}
        assert requested_points.isdisjoint(HIDDEN_WRITE_SAMPLES)


@pytest.mark.asyncio
async def test_user_sees_every_guessed_opendata_capability_after_setup(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(capability_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        assert set(entry_entities(hass, entry)) == expected_unique_ids()
        for capability in GET_USER_CAPABILITIES:
            assert_get_state(hass, entry, capability)
        for capability in SET_USER_CAPABILITIES:
            if capability.user_visible:
                assert_set_entity(hass, entry, capability)


@pytest.mark.asyncio
async def test_bk_user_sees_every_guessed_opendata_capability_after_setup(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(bk_capability_backend_data())
    install_fake_devices(monkeypatch, {BK_HOST: backend})
    entry = make_entry(host=BK_HOST, serial=BK_SERIAL, model=BK_MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        expected = BK_ALWAYS_PRESENT_UNIQUE_IDS | {
            capability.unique_id(BK_SERIAL) for capability in BK_GET_USER_CAPABILITIES
        }
        assert set(entry_entities(hass, entry)) == expected
        for capability in BK_GET_USER_CAPABILITIES:
            assert_get_state(hass, entry, capability, serial=BK_SERIAL)


@pytest.mark.asyncio
async def test_non_user_getdata_points_do_not_create_duplicate_ha_items(
    monkeypatch,
    tmp_path,
) -> None:
    default_backend = FakeDevice(
        capability_backend_data()
        | {str(point): "NON-USER" for point in DEFAULT_NON_USER_READ_POINTS}
    )
    bk_backend = FakeDevice(
        bk_capability_backend_data()
        | {str(point): "NON-USER" for point in BK_NON_USER_READ_POINTS}
    )
    install_fake_devices(
        monkeypatch,
        {HOST: default_backend, BK_HOST: bk_backend},
    )
    default_entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)
    bk_entry = make_entry(host=BK_HOST, serial=BK_SERIAL, model=BK_MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, default_entry)
        await add_entry(hass, bk_entry)

        default_requested = {
            point for batch in default_backend.fetches for point in batch
        }
        bk_requested = {point for batch in bk_backend.fetches for point in batch}
        assert default_requested.isdisjoint(DEFAULT_NON_USER_READ_POINTS)
        assert bk_requested.isdisjoint(BK_NON_USER_READ_POINTS)
        assert not {
            f"{SERIAL}_{point}" for point in DEFAULT_NON_USER_READ_POINTS
        } & set(entry_entities(hass, default_entry))
        assert not {f"{BK_SERIAL}_{point}" for point in BK_NON_USER_READ_POINTS} & set(
            entry_entities(hass, bk_entry)
        )

        default_device = device_for_serial(hass, SERIAL)
        bk_device = device_for_serial(hass, BK_SERIAL)
        assert default_device is not None
        assert default_device.serial_number == SERIAL
        assert bk_device is not None
        assert bk_device.serial_number == BK_SERIAL


@pytest.mark.asyncio
async def test_user_can_enable_and_operate_every_guessed_opendata_control(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(capability_backend_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        registry = er.async_get(hass)

        for capability in SET_USER_CAPABILITIES:
            if capability.user_visible and not capability.enabled_by_default:
                registry_entry = entry_entities(hass, entry)[set_unique_id(capability)]
                registry.async_update_entity(
                    registry_entry.entity_id,
                    disabled_by=None,
                )

        # The existing unload bug has its own strict lifecycle test. Supply the
        # cleanup reference here only so this scenario can reload enabled entities.
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.runtime_data
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        for capability in SET_USER_CAPABILITIES:
            if not capability.user_visible:
                continue

            registry_entry = entry_entities(hass, entry)[set_unique_id(capability)]
            before = len(backend.writes)
            if capability.entity_domain == "number":
                service = "set_value"
                service_data = {
                    "entity_id": registry_entry.entity_id,
                    "value": capability.user_value,
                }
            elif capability.entity_domain == "select":
                service = "select_option"
                service_data = {
                    "entity_id": registry_entry.entity_id,
                    "option": capability.user_value,
                }
            else:
                service = "set_value"
                service_data = {
                    "entity_id": registry_entry.entity_id,
                    "time": capability.user_value,
                }

            await hass.services.async_call(
                capability.entity_domain,
                service,
                service_data,
                blocking=True,
            )
            await hass.async_block_till_done()

            assert backend.writes[before:] == [
                (capability.point, [capability.wire_value])
            ]
