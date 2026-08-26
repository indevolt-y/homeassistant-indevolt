"""Fixed Home Assistant user scenarios distilled from SF3000 device tests."""

from __future__ import annotations

from datetime import time
from itertools import cycle

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EntityCategory
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr

from custom_components.indevolt.const import DOMAIN
from tests.integration._support import (
    DEFAULT_DATA,
    FakeDevice,
    add_entry,
    configure_user_flow,
    device_for_serial,
    entry_entities,
    home_assistant_runtime,
    install_fake_devices,
    make_entry,
)
from tests.models._opendata_user_testing import assert_entity_translation

MODEL = "SolidFlex/PowerFlex2000"
REPORTED_MODEL = "CMS-SF2000"
SERIAL = "SF3000-SCENARIO-SN"
HOST = "192.0.2.200"

PACK_SERIAL_POINTS = {
    1: "9032",
    2: "9051",
    3: "9070",
    4: "9165",
    5: "9218",
}


def scenario_data(
    values: dict[int | str, object] | None = None,
    *,
    pack_serials: dict[int, str] | None = None,
) -> dict[str, object]:
    """Build one deterministic software-only device response."""
    data: dict[str, object] = dict(DEFAULT_DATA)
    for point in PACK_SERIAL_POINTS.values():
        data.pop(point, None)

    selected_packs = {1: "PACK-1"} if pack_serials is None else pack_serials
    data.update(
        {
            PACK_SERIAL_POINTS[pack_id]: serial
            for pack_id, serial in selected_packs.items()
        }
    )
    if values is not None:
        data.update({str(point): value for point, value in values.items()})
    return data


def require_registry_entity(hass, entry, unique_id: str):
    """Return one expected entity with a useful TDD failure message."""
    entities = entry_entities(hass, entry)
    assert unique_id in entities, f"expected Home Assistant entity {unique_id}"
    return entities[unique_id]


def require_state(hass, entry, unique_id: str):
    """Return one expected loaded state."""
    registry_entry = require_registry_entity(hass, entry, unique_id)
    state = hass.states.get(registry_entry.entity_id)
    assert state is not None, f"expected loaded state for {unique_id}"
    return state


def require_named_state(hass, name_suffix: str):
    """Find one user-visible state by the end of its friendly name."""
    matches = [
        state
        for state in hass.states.async_all()
        if str(state.attributes.get("friendly_name", "")).endswith(name_suffix)
    ]
    assert len(matches) == 1, (
        f"expected one entity named *{name_suffix!r}, found {len(matches)}"
    )
    return matches[0]


def integration_device_identifiers(hass) -> set[tuple[str, str]]:
    """Return identifiers of devices created by this integration only."""
    return {
        identifier
        for device in dr.async_get(hass).devices.values()
        for identifier in device.identifiers
        if identifier[0] == DOMAIN
    }


async def refresh_with(hass, entry, backend: FakeDevice, values) -> None:
    """Apply a later mocked device response and run a real coordinator refresh."""
    backend.data.update({str(point): value for point, value in values.items()})
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


async def set_number(hass, entry, key: str, value: int | float) -> None:
    entity = require_registry_entity(hass, entry, f"{entry.unique_id}_{key}")
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity.entity_id, "value": value},
        blocking=True,
    )
    await hass.async_block_till_done()


async def select_option(hass, entry, key: str, option: str) -> None:
    entity = require_registry_entity(hass, entry, f"{entry.unique_id}_{key}")
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity.entity_id, "option": option},
        blocking=True,
    )
    await hass.async_block_till_done()


async def call_work_mode_action(
    hass,
    serial: str,
    *,
    state: str,
    power: int,
    soc: int,
) -> None:
    device = device_for_serial(hass, serial)
    assert device is not None
    await hass.services.async_call(
        DOMAIN,
        "set_solidflex_powerflex_work_mode",
        {
            "device_id": [device.id],
            "mode": "Real-Time Control",
            "state": state,
            "power": power,
            "soc": soc,
        },
        blocking=True,
    )
    await hass.async_block_till_done()


async def assert_realtime_soc_scenario(
    monkeypatch,
    tmp_path,
    *,
    host: str,
    initial_soc: float,
    requested_state: str,
    wire_state: int,
    requested_power: int,
    target_soc: int,
) -> None:
    """Exercise one charge/discharge journey through the real HA action."""
    backend = FakeDevice(scenario_data({6002: initial_soc}))

    async def apply_realtime_write(point, value) -> None:
        if point == 47015:
            backend.data["6001"] = 1000 + int(value[0])
            backend.data["6002"] = int(value[2])

    backend.before_write = apply_realtime_write
    install_fake_devices(monkeypatch, {host: backend})
    entry = make_entry(host=host, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        assert require_state(hass, entry, f"{SERIAL}_6002").state == str(initial_soc)

        await call_work_mode_action(
            hass,
            SERIAL,
            state=requested_state,
            power=requested_power,
            soc=target_soc,
        )

        assert backend.writes == [
            (47005, [4]),
            (47015, [wire_state, requested_power, target_soc]),
        ]
        assert require_state(hass, entry, f"{SERIAL}_6002").state == str(target_soc)


@pytest.mark.asyncio
async def test_f_01_user_sees_the_fixed_sf3000_firmware_set(
    monkeypatch,
    tmp_path,
) -> None:
    """F-01: CMS, P-file, EMS, BMS-MB, INV, and DCDC stay distinguishable."""
    cms = "V1.4.0C_R020.092_M4801_00000036"
    pfile = "R00D.001_P4801_00000019"
    backend = FakeDevice(
        scenario_data({1118: 10006, 1109: 12008, 1119: 321, 1120: 14015}),
        config={
            "device": {
                "type": REPORTED_MODEL,
                "sn": SERIAL,
                "f_ver": cms,
                "p_ver": pfile,
            }
        },
    )
    install_fake_devices(monkeypatch, {HOST: backend})

    async with home_assistant_runtime(tmp_path) as hass:
        result = await configure_user_flow(hass, host=HOST)
        await hass.async_block_till_done()
        assert result["type"] == "create_entry"

        entry = hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, SERIAL)
        assert entry is not None
        assert entry.state is ConfigEntryState.LOADED
        device = device_for_serial(hass, SERIAL)
        assert device is not None
        assert device.sw_version == cms
        assert require_state(hass, entry, f"{SERIAL}_1118").state == "1.00.06"
        assert require_state(hass, entry, f"{SERIAL}_1109").state == "1.20.08"
        assert require_state(hass, entry, f"{SERIAL}_1119").state == "3.21"
        assert require_state(hass, entry, f"{SERIAL}_1120").state == "1.40.15"
        pfile_entity = require_registry_entity(hass, entry, f"{SERIAL}_p_ver")
        assert pfile_entity.domain == "sensor"
        assert pfile_entity.translation_key == "p_file_version"
        assert pfile_entity.entity_category is EntityCategory.DIAGNOSTIC
        assert pfile_entity.has_entity_name is True
        assert pfile_entity.device_id == device.id

        pfile_state = hass.states.get(pfile_entity.entity_id)
        assert pfile_state is not None
        assert pfile_state.state == pfile
        assert pfile_state.attributes["friendly_name"].endswith("P-file Version")
        assert pfile_state.attributes.get("device_class") is None
        assert pfile_state.attributes.get("state_class") is None
        assert pfile_state.attributes.get("unit_of_measurement") is None
        assert_entity_translation(
            "sensor",
            "p_file_version",
            "P-file Version",
            None,
        )


@pytest.mark.asyncio
async def test_f_01_missing_pfile_version_creates_no_placeholder_entity(
    monkeypatch,
    tmp_path,
) -> None:
    """F-01: an omitted optional P-file value never becomes a fake entity."""
    backend = FakeDevice(
        scenario_data(),
        config={
            "device": {
                "type": REPORTED_MODEL,
                "sn": SERIAL,
                "f_ver": "V1.4.0C_R020.092_M4801_00000036",
            }
        },
    )
    install_fake_devices(monkeypatch, {HOST: backend})

    async with home_assistant_runtime(tmp_path) as hass:
        result = await configure_user_flow(hass, host=HOST)
        await hass.async_block_till_done()
        assert result["type"] == "create_entry"

        entry = hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, SERIAL)
        assert entry is not None
        assert f"{SERIAL}_p_ver" not in entry_entities(hass, entry)


@pytest.mark.asyncio
async def test_f_02_sf3000_ac_creates_no_pv_entities(
    monkeypatch,
    tmp_path,
) -> None:
    """F-02: a fixed AC-only response reports zero MPPTs and no PV entities."""
    backend = FakeDevice(scenario_data({120: 0}, pack_serials={}))
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        pv_points = {1501, 1600, 1601, 1602, 1603, 1632, 1633, 1634, 1635}
        assert {f"{SERIAL}_{point}" for point in pv_points}.isdisjoint(
            entry_entities(hass, entry)
        )
        assert require_named_state(hass, "Maximum MPPT Channels").state == "0"


@pytest.mark.asyncio
async def test_f_03_two_physical_battery_packs_create_exactly_two_children(
    monkeypatch,
    tmp_path,
) -> None:
    """F-03: one PFA2000 and one PFA4000 never become six child devices."""
    backend = FakeDevice(
        scenario_data(
            {9016: 51, 9035: 52},
            pack_serials={1: "PFA2000-SN", 2: "PFA4000-SN"},
        )
    )
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        assert integration_device_identifiers(hass) == {
            (DOMAIN, SERIAL),
            (DOMAIN, "battery_1_PFA2000-SN"),
            (DOMAIN, "battery_2_PFA4000-SN"),
        }


@pytest.mark.asyncio
async def test_f_04_whole_master_and_slave_soc_values_do_not_mix(
    monkeypatch,
    tmp_path,
) -> None:
    """F-04: total, master-pack, and slave-pack SOC retain separate values."""
    backend = FakeDevice(
        scenario_data(
            {6002: 74.9, 9000: 74.5, 9016: 75.1},
            pack_serials={1: "PFA-SLAVE-1"},
        )
    )
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        assert require_state(hass, entry, f"{SERIAL}_6002").state == "74.9"
        assert require_state(hass, entry, f"{SERIAL}_9000").state == "74.5"
        assert require_state(hass, entry, f"{SERIAL}_battery_1_9016").state == "75.1"


@pytest.mark.asyncio
async def test_f_05_sf2000_with_one_4000_pack_keeps_pack_identity(
    monkeypatch,
    tmp_path,
) -> None:
    """F-05: a reused 4000 pack remains one child of the correct main device."""
    backend = FakeDevice(scenario_data({9016: 68.6}, pack_serials={1: "PFA4000-SN"}))
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        main_device = device_for_serial(hass, SERIAL)
        pack_device = device_for_serial(hass, "battery_1_PFA4000-SN")
        assert main_device is not None
        assert pack_device is not None
        assert pack_device.via_device_id == main_device.id
        assert require_state(hass, entry, f"{SERIAL}_battery_1_9016").state == "68.6"
        assert device_for_serial(hass, "battery_2_PFA4000-SN") is None


@pytest.mark.asyncio
async def test_f_06_wired_parallel_topology_preserves_feed_in_limit(
    monkeypatch,
    tmp_path,
) -> None:
    """F-06: wired topology keeps the existing 2400 W feed-in limit."""
    master = FakeDevice(
        scenario_data({606: "1000", 669: 0}, pack_serials={1: "WIRED-M-PACK"})
    )
    slave = FakeDevice(
        scenario_data({606: "1001", 669: 0}, pack_serials={1: "WIRED-S-PACK"})
    )
    install_fake_devices(
        monkeypatch,
        {"192.0.2.206": master, "192.0.2.207": slave},
    )
    master_entry = make_entry(host="192.0.2.206", serial="WIRED-MASTER-SN", model=MODEL)
    slave_entry = make_entry(host="192.0.2.207", serial="WIRED-SLAVE-SN", model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, master_entry)
        await add_entry(hass, slave_entry)
        assert require_state(hass, master_entry, "WIRED-MASTER-SN_606").state == (
            "Master"
        )
        assert require_state(hass, slave_entry, "WIRED-SLAVE-SN_606").state == ("Slave")
        assert require_state(hass, master_entry, "WIRED-MASTER-SN_669").state == (
            "centralized"
        )
        assert require_state(hass, slave_entry, "WIRED-SLAVE-SN_669").state == (
            "centralized"
        )

        feed_in = require_state(
            hass,
            master_entry,
            "WIRED-MASTER-SN_feed_in_power_limit",
        )
        assert feed_in.attributes["max"] == 2400

        await set_number(hass, master_entry, "feed_in_power_limit", 2400)
        assert len(master.writes) == 1
        assert slave.writes == []

        with pytest.raises(
            ServiceValidationError,
            match=r"outside valid range 50(?:\.0)? - 2400(?:\.0)?",
        ):
            await set_number(hass, master_entry, "feed_in_power_limit", 3600)

        assert len(master.writes) == 1
        assert slave.writes == []


@pytest.mark.asyncio
async def test_f_07_wireless_parallel_topology_preserves_feed_in_limit(
    monkeypatch,
    tmp_path,
) -> None:
    """F-07: wireless topology keeps the existing 2400 W feed-in limit."""
    master = FakeDevice(
        scenario_data({606: "1000", 669: 1}, pack_serials={1: "RADIO-M-PACK"})
    )
    slave = FakeDevice(
        scenario_data({606: "1001", 669: 1}, pack_serials={1: "RADIO-S-PACK"})
    )
    install_fake_devices(
        monkeypatch,
        {"192.0.2.208": master, "192.0.2.209": slave},
    )
    master_entry = make_entry(host="192.0.2.208", serial="RADIO-MASTER-SN", model=MODEL)
    slave_entry = make_entry(host="192.0.2.209", serial="RADIO-SLAVE-SN", model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, master_entry)
        await add_entry(hass, slave_entry)
        assert require_state(hass, master_entry, "RADIO-MASTER-SN_606").state == (
            "Master"
        )
        assert require_state(hass, slave_entry, "RADIO-SLAVE-SN_606").state == ("Slave")
        assert require_state(hass, master_entry, "RADIO-MASTER-SN_669").state == (
            "coordinated"
        )
        assert require_state(hass, slave_entry, "RADIO-SLAVE-SN_669").state == (
            "coordinated"
        )

        feed_in = require_state(
            hass,
            master_entry,
            "RADIO-MASTER-SN_feed_in_power_limit",
        )
        assert feed_in.attributes["max"] == 2400

        await set_number(hass, master_entry, "feed_in_power_limit", 2400)
        assert len(master.writes) == 1
        assert slave.writes == []

        with pytest.raises(
            ServiceValidationError,
            match=r"outside valid range 50(?:\.0)? - 2400(?:\.0)?",
        ):
            await set_number(hass, master_entry, "feed_in_power_limit", 10_800)

        assert len(master.writes) == 1
        assert slave.writes == []


@pytest.mark.asyncio
async def test_f_08_user_sees_the_connected_mr1_meter(
    monkeypatch,
    tmp_path,
) -> None:
    """F-08: the fixed MR1 meter response appears on the main device."""
    backend = FakeDevice(scenario_data({7120: 1000, 11016: 2953}))
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        meter_status = require_state(hass, entry, f"{SERIAL}_7120")
        meter_power = require_state(hass, entry, f"{SERIAL}_11016")
        main_device = device_for_serial(hass, SERIAL)
        assert main_device is not None
        assert meter_status.state == "ON"
        assert meter_power.state == "2953"
        assert meter_status.attributes.get("unit_of_measurement") is None
        assert meter_power.attributes["unit_of_measurement"] == "W"
        assert require_registry_entity(hass, entry, f"{SERIAL}_7120").device_id == (
            main_device.id
        )
        assert require_registry_entity(hass, entry, f"{SERIAL}_11016").device_id == (
            main_device.id
        )


@pytest.mark.asyncio
async def test_f_09_all_four_load_sources_write_without_inventing_readback(
    monkeypatch,
    tmp_path,
) -> None:
    """F-09: all load choices write while the existing state stays unknown."""
    backend = FakeDevice(scenario_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        for expected_value, option in enumerate(
            ("Smart Plug", "Meter", "Key Load", "Custom"),
            start=1,
        ):
            await select_option(hass, entry, "load_setting", option)
            assert backend.writes[-1] == (1, [expected_value])
            assert require_state(hass, entry, f"{SERIAL}_load_setting").state == (
                "unknown"
            )

        assert backend.writes == [(1, [1]), (1, [2]), (1, [3]), (1, [4])]


@pytest.mark.asyncio
async def test_f_10_self_consumption_mode_round_trips(
    monkeypatch,
    tmp_path,
) -> None:
    """F-10: Self-Consumed Prioritized stays readable and writable."""
    backend = FakeDevice(scenario_data({7101: 1}))
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        assert require_state(hass, entry, f"{SERIAL}_work_mode").state == (
            "Self-Consumed Prioritized"
        )
        await select_option(hass, entry, "work_mode", "Self-Consumed Prioritized")
        assert backend.writes == [(47005, [1])]
        assert require_state(hass, entry, f"{SERIAL}_work_mode").state == (
            "Self-Consumed Prioritized"
        )


@pytest.mark.asyncio
async def test_f_11_realtime_charge_reaches_55_percent(
    monkeypatch,
    tmp_path,
) -> None:
    """F-11: 52.2%, charge 1000 W, and target 55% form one journey."""
    await assert_realtime_soc_scenario(
        monkeypatch,
        tmp_path,
        host="192.0.2.211",
        initial_soc=52.2,
        requested_state="Charging",
        wire_state=1,
        requested_power=1000,
        target_soc=55,
    )


@pytest.mark.asyncio
async def test_f_12_realtime_discharge_reaches_55_percent(
    monkeypatch,
    tmp_path,
) -> None:
    """F-12: 58.5%, discharge 1000 W, and target 55% form one journey."""
    await assert_realtime_soc_scenario(
        monkeypatch,
        tmp_path,
        host="192.0.2.212",
        initial_soc=58.5,
        requested_state="Discharging",
        wire_state=2,
        requested_power=1000,
        target_soc=55,
    )


@pytest.mark.asyncio
async def test_f_13_realtime_standby_keeps_zero_watts_and_100_percent(
    monkeypatch,
    tmp_path,
) -> None:
    """F-13: standby, 0 W, and 100% are not rewritten by the integration."""
    backend = FakeDevice(scenario_data({6002: 54.3, 6001: 1000, 1501: 800}))

    async def apply_realtime_write(point, value) -> None:
        if point == 47015:
            backend.data["6001"] = 1000 + int(value[0])

    backend.before_write = apply_realtime_write
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        await call_work_mode_action(
            hass,
            SERIAL,
            state="Standby",
            power=0,
            soc=100,
        )
        assert backend.writes == [(47005, [4]), (47015, [0, 0, 100])]
        assert require_state(hass, entry, f"{SERIAL}_state_setting").state == (
            "Standby"
        )
        assert require_state(hass, entry, f"{SERIAL}_1501").state == "800"


@pytest.mark.asyncio
async def test_f_14_every_fixed_realtime_input_is_preserved(
    monkeypatch,
    tmp_path,
) -> None:
    """F-14: every power and target-SOC value recorded by the source is sent."""
    backend = FakeDevice(scenario_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)
    powers = (0, 500, 800, 900, 1000, 1500, 2000, 2500, 3000)
    target_socs = cycle((5, 55, 58, 100))
    expected_writes: list[tuple[int, list[int]]] = []

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        for power in powers:
            target_soc = next(target_socs)
            state = "Standby" if power == 0 else "Charging"
            wire_state = 0 if power == 0 else 1
            await call_work_mode_action(
                hass,
                SERIAL,
                state=state,
                power=power,
                soc=target_soc,
            )
            expected_writes.extend(
                [(47005, [4]), (47015, [wire_state, power, target_soc])]
            )

        assert backend.writes == expected_writes


@pytest.mark.asyncio
async def test_f_15_one_master_and_two_slave_packs_keep_soc_and_controls(
    monkeypatch,
    tmp_path,
) -> None:
    """F-15: a low-SOC topology keeps child identity, Backup SOC, and AC charging."""
    backend = FakeDevice(
        scenario_data(
            {9000: 0, 9016: 0, 9035: 1, 6105: 5, 2618: 1001},
            pack_serials={1: "LOW-SOC-PACK-1", 2: "LOW-SOC-PACK-2"},
        )
    )
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        assert require_state(hass, entry, f"{SERIAL}_9000").state == "0"
        assert require_state(hass, entry, f"{SERIAL}_battery_1_9016").state == "0"
        assert require_state(hass, entry, f"{SERIAL}_battery_2_9035").state == "1"
        assert require_state(hass, entry, f"{SERIAL}_backup_soc").state == "5"
        assert require_state(hass, entry, f"{SERIAL}_grid").state == "on"
        assert device_for_serial(hass, "battery_1_LOW-SOC-PACK-1") is not None
        assert device_for_serial(hass, "battery_2_LOW-SOC-PACK-2") is not None


@pytest.mark.asyncio
async def test_f_16_forced_full_charge_settings_survive_reload(
    monkeypatch,
    tmp_path,
) -> None:
    """F-16: all forced full-charge settings remain after an HA reload."""
    backend = FakeDevice(scenario_data({1127: 15, 8646: 1, 8647: 0x0800, 2802: 100}))

    async def remember_settings(point, value) -> None:
        if point in {8646, 8647, 2802}:
            backend.data[str(point)] = value[0]

    backend.before_write = remember_settings
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        interval = require_registry_entity(
            hass, entry, f"{SERIAL}_forced_full_charge_interval"
        )
        start = require_registry_entity(
            hass, entry, f"{SERIAL}_forced_full_charge_start_time"
        )
        power = require_registry_entity(
            hass, entry, f"{SERIAL}_forced_ac_charging_power"
        )
        original_unique_ids = set(entry_entities(hass, entry))

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": interval.entity_id, "value": 1},
            blocking=True,
        )
        await hass.services.async_call(
            "time",
            "set_value",
            {"entity_id": start.entity_id, "time": time(8, 0)},
            blocking=True,
        )
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": power.entity_id, "value": 100},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert backend.writes == [(8646, [1]), (8647, [0x0800]), (2802, [100])]

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.runtime_data
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert set(entry_entities(hass, entry)) == original_unique_ids
        assert (
            require_state(hass, entry, f"{SERIAL}_forced_full_charge_interval").state
            == "1"
        )
        assert (
            require_state(hass, entry, f"{SERIAL}_forced_full_charge_start_time").state
            == "08:00:00"
        )
        assert (
            require_state(hass, entry, f"{SERIAL}_forced_ac_charging_power").state
            == "100"
        )


@pytest.mark.asyncio
async def test_f_17_deep_sleep_updates_existing_soc_entities_without_waiting(
    monkeypatch,
    tmp_path,
) -> None:
    """F-17: fixed response frames replace a real two-minute hardware wait."""
    backend = FakeDevice(
        scenario_data(
            {
                1127: 15,
                35001: 0x121E,
                35002: 0x061E,
                11006: 4,
                9000: 56.6,
                9016: 68.6,
            },
            pack_serials={1: "SLEEP-PACK-1"},
        )
    )
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        start = require_registry_entity(hass, entry, f"{SERIAL}_deep_sleep_start_time")
        end = require_registry_entity(hass, entry, f"{SERIAL}_deep_sleep_end_time")
        stable_ids = {
            require_registry_entity(hass, entry, f"{SERIAL}_11006").id,
            require_registry_entity(hass, entry, f"{SERIAL}_9000").id,
            require_registry_entity(hass, entry, f"{SERIAL}_battery_1_9016").id,
        }

        await hass.services.async_call(
            "time",
            "set_value",
            {"entity_id": start.entity_id, "time": time(18, 30)},
            blocking=True,
        )
        await hass.services.async_call(
            "time",
            "set_value",
            {"entity_id": end.entity_id, "time": time(6, 30)},
            blocking=True,
        )
        await refresh_with(
            hass,
            entry,
            backend,
            {11006: 14, 9000: 52.5, 9016: 68},
        )

        assert require_state(hass, entry, f"{SERIAL}_11006").state == "deep_sleep"
        assert require_state(hass, entry, f"{SERIAL}_9000").state == "52.5"
        assert require_state(hass, entry, f"{SERIAL}_battery_1_9016").state == "68"
        assert stable_ids == {
            require_registry_entity(hass, entry, f"{SERIAL}_11006").id,
            require_registry_entity(hass, entry, f"{SERIAL}_9000").id,
            require_registry_entity(hass, entry, f"{SERIAL}_battery_1_9016").id,
        }


@pytest.mark.asyncio
async def test_f_18_bypass_off_on_off_keeps_one_entity_and_power(
    monkeypatch,
    tmp_path,
) -> None:
    """F-18: three bypass operations update one switch and preserve 2953 W."""
    backend = FakeDevice(scenario_data({680: 1, 667: 2953}))

    async def remember_bypass(point, value) -> None:
        if point == 7266:
            backend.data["680"] = value[0]

    backend.before_write = remember_bypass
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        switch = require_registry_entity(hass, entry, f"{SERIAL}_bypass")
        original_registry_id = switch.id

        for service, expected_state in (
            ("turn_off", "off"),
            ("turn_on", "on"),
            ("turn_off", "off"),
        ):
            await hass.services.async_call(
                "switch",
                service,
                {"entity_id": switch.entity_id},
                blocking=True,
            )
            await refresh_with(hass, entry, backend, {})
            assert require_state(hass, entry, f"{SERIAL}_bypass").state == (
                expected_state
            )

        assert backend.writes == [(7266, [0]), (7266, [1]), (7266, [0])]
        assert require_registry_entity(hass, entry, f"{SERIAL}_bypass").id == (
            original_registry_id
        )
        assert require_state(hass, entry, f"{SERIAL}_667").state == "2953"


@pytest.mark.asyncio
async def test_f_19_fixed_power_and_energy_values_have_correct_units(
    monkeypatch,
    tmp_path,
) -> None:
    """F-19: recorded values become distinct HA power and energy entities."""
    backend = FakeDevice(
        scenario_data(
            {
                8500: 3008,
                11007: 911,
                1502: 0.696,
                2105: 0.530,
                11037: 530,
                11034: 527,
                11035: 527,
                9284: 177,
                9285: 177,
            }
        )
    )
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    expected = (
        ("Total PV Charging Power", "3008", "W"),
        ("Total Inverter Input Energy", "911", "Wh"),
        ("Daily Production", "0.696", "kWh"),
        ("Off-grid Output Energy", "0.53", "kWh"),
        ("Daily Off-grid Discharge Energy", "530", "Wh"),
        ("Bypass Input Energy", "527", "Wh"),
        ("Total Bypass Port Discharge Energy", "177", "Wh"),
        ("Daily Bypass Discharge Energy", "177", "Wh"),
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        for name, state_value, unit in expected:
            state = require_named_state(hass, name)
            assert state.state == state_value
            assert state.attributes.get("unit_of_measurement") == unit
        assert f"{SERIAL}_11035" not in entry_entities(hass, entry)


@pytest.mark.asyncio
async def test_f_20_firmware_change_and_restart_preserve_device_identity(
    monkeypatch,
    tmp_path,
) -> None:
    """F-20: restart updates data without duplicating the device or entities."""
    backend = FakeDevice(scenario_data({1118: 10006, 6002: 47.3, 7101: 1}))
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(
        host=HOST,
        serial=SERIAL,
        model=MODEL,
        firmware="V1.4.0C_R020.092_M4801_00000036",
    )

    async with home_assistant_runtime(tmp_path, writable_storage=True) as hass:
        await add_entry(hass, entry)
        original_device = device_for_serial(hass, SERIAL)
        assert original_device is not None
        original_device_id = original_device.id
        original_entities = {
            unique_id: registry_entry.id
            for unique_id, registry_entry in entry_entities(hass, entry).items()
        }

    backend.data["1118"] = 10007

    async with home_assistant_runtime(tmp_path, restore=True) as hass:
        restored_entry = hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN, SERIAL
        )
        assert restored_entry is not None
        assert restored_entry.state is ConfigEntryState.LOADED
        restored_device = device_for_serial(hass, SERIAL)
        assert restored_device is not None
        assert restored_device.id == original_device_id
        assert {
            unique_id: registry_entry.id
            for unique_id, registry_entry in entry_entities(
                hass, restored_entry
            ).items()
        } == original_entities
        assert require_state(hass, restored_entry, f"{SERIAL}_1118").state == (
            "1.00.07"
        )
        assert require_state(hass, restored_entry, f"{SERIAL}_6002").state == ("47.3")
        assert require_state(hass, restored_entry, f"{SERIAL}_work_mode").state == (
            "Self-Consumed Prioritized"
        )


@pytest.mark.asyncio
async def test_f_21_pv_undervoltage_and_recovery_update_the_same_entities(
    monkeypatch,
    tmp_path,
) -> None:
    """F-21: three response frames replace a real 15-minute recovery wait."""
    backend = FakeDevice(scenario_data({7119: 4, 8138: 0, 1600: 30.0}))
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        status = require_registry_entity(hass, entry, f"{SERIAL}_7119")
        alarm = require_registry_entity(hass, entry, f"{SERIAL}_8138")
        stable_ids = (status.id, alarm.id)

        await refresh_with(hass, entry, backend, {7119: 2, 8138: 21, 1600: 12.6})
        assert require_state(hass, entry, f"{SERIAL}_7119").state == "sleep"
        assert require_state(hass, entry, f"{SERIAL}_8138").state == (
            "pv_input_undervoltage"
        )
        assert require_state(hass, entry, f"{SERIAL}_1600").state == "12.6"

        await refresh_with(hass, entry, backend, {7119: 4, 8138: 0, 1600: 30.0})
        assert require_state(hass, entry, f"{SERIAL}_7119").state == "running"
        assert require_state(hass, entry, f"{SERIAL}_8138").state == "unknown"
        assert stable_ids == (
            require_registry_entity(hass, entry, f"{SERIAL}_7119").id,
            require_registry_entity(hass, entry, f"{SERIAL}_8138").id,
        )


@pytest.mark.asyncio
async def test_f_22_two_pack_heater_cycles_keep_pack_ownership(
    monkeypatch,
    tmp_path,
) -> None:
    """F-22: temperature, heater state, and 37.9 W stay on the right pack."""
    backend = FakeDevice(
        scenario_data(
            {9081: 5.0, 9082: 0, 9080: 0, 9097: 6.0, 9098: 0, 9096: 0},
            pack_serials={1: "HEATER-PACK-1"},
        )
    )
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        master_heater = require_registry_entity(hass, entry, f"{SERIAL}_9080")
        pack_heater = require_registry_entity(hass, entry, f"{SERIAL}_battery_1_9096")
        main_device = device_for_serial(hass, SERIAL)
        pack_device = device_for_serial(hass, "battery_1_HEATER-PACK-1")
        assert main_device is not None
        assert pack_device is not None
        assert master_heater.device_id == main_device.id
        assert pack_heater.device_id == pack_device.id

        frames = (
            {9081: 0.5, 9082: 37.9, 9080: 1, 9097: 0.7, 9098: 37.9, 9096: 1},
            {9081: 5.5, 9082: 0, 9080: 0, 9097: 5.8, 9098: 0, 9096: 0},
            {9081: 0.4, 9082: 37.9, 9080: 1, 9097: 0.6, 9098: 37.9, 9096: 1},
        )
        expected_states = (("on", "on"), ("off", "off"), ("on", "on"))
        for frame, (master_state, pack_state) in zip(
            frames, expected_states, strict=True
        ):
            await refresh_with(hass, entry, backend, frame)
            assert require_state(hass, entry, f"{SERIAL}_9080").state == (master_state)
            assert (
                require_state(hass, entry, f"{SERIAL}_battery_1_9096").state
                == pack_state
            )

        assert require_state(hass, entry, f"{SERIAL}_9082").state == "37.9"
        assert require_state(hass, entry, f"{SERIAL}_battery_1_9098").state == "37.9"


@pytest.mark.asyncio
async def test_f_23_missing_master_heater_fault_source_creates_no_entity(
    monkeypatch,
    tmp_path,
) -> None:
    """F-23: HA does not invent a fault entity without an OpenData source."""
    backend = FakeDevice(scenario_data())
    install_fake_devices(monkeypatch, {HOST: backend})
    entry = make_entry(host=HOST, serial=SERIAL, model=MODEL)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        matches = [
            state
            for state in hass.states.async_all()
            if str(state.attributes.get("friendly_name", "")).endswith(
                "Master Battery Heater Fault"
            )
        ]
        assert matches == []
