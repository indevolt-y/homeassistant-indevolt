"""Real Home Assistant registration contracts for the two runtime routes."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr

from custom_components.indevolt.const import DOMAIN

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


@pytest.mark.asyncio
async def test_default_entry_loads_entities_states_and_device_hierarchy(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.10": backend})
    entry = make_entry(
        host="192.0.2.10",
        serial="SF-SN",
        model="SolidFlex/PowerFlex2000",
    )
    original_data = dict(entry.data)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        assert entry.state is ConfigEntryState.LOADED
        assert dict(entry.data) == original_data
        assert set(entry_entities(hass, entry)) == {
            "SF-SN_work_mode",
            "SF-SN_state_setting",
            "SF-SN_load_setting",
            "SF-SN_led_light_strip_mode",
            "SF-SN_light",
            "SF-SN_grid",
            "SF-SN_bypass",
            "SF-SN_backup_soc",
            "SF-SN_inverter_input_limit",
            "SF-SN_max_output_power",
            "SF-SN_feed_in_power_limit",
            "SF-SN_power_setting",
            "SF-SN_soc_setting",
            "SF-SN_1118",
            "SF-SN_142",
            "SF-SN_battery_1_9016",
        }
        assert {
            unique_id: state_for_unique_id(hass, entry, unique_id).state
            for unique_id in entry_entities(hass, entry)
        } == {
            "SF-SN_work_mode": "Self-Consumed Prioritized",
            "SF-SN_state_setting": "Charging",
            "SF-SN_load_setting": "unknown",
            "SF-SN_led_light_strip_mode": "on",
            "SF-SN_light": "on",
            "SF-SN_grid": "on",
            "SF-SN_bypass": "off",
            "SF-SN_backup_soc": "50",
            "SF-SN_inverter_input_limit": "1000",
            "SF-SN_max_output_power": "1200",
            "SF-SN_feed_in_power_limit": "800",
            "SF-SN_power_setting": "unknown",
            "SF-SN_soc_setting": "unknown",
            "SF-SN_1118": "1.23.45",
            "SF-SN_142": "2048",
            "SF-SN_battery_1_9016": "51",
        }

        main_device = device_for_serial(hass, "SF-SN")
        battery_device = device_for_serial(hass, "battery_1_PACK-1")
        assert main_device is not None
        assert main_device.name == "SolidFlex/PowerFlex2000 (SF-SN)"
        assert main_device.model == "SolidFlex/PowerFlex2000"
        assert main_device.sw_version == "1.2.3"
        assert battery_device is not None
        assert battery_device.name == "SFA/PFA Battery Pack 1 (PACK-1)"
        assert battery_device.via_device_id == main_device.id
        assert hass.services.has_service(
            DOMAIN,
            "set_solidflex_powerflex_work_mode",
        )
        assert hass.services.has_service(DOMAIN, "set_bk1600_work_mode")


@pytest.mark.asyncio
async def test_bk_entry_loads_only_its_existing_platform_contract(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(
        {
            "1664": 800,
            "1505": 2500,
            "6001": 1001,
            "7101": 4,
            "7120": 1000,
        }
    )
    install_fake_devices(monkeypatch, {"192.0.2.20": backend})
    entry = make_entry(
        host="192.0.2.20",
        serial="BK-SN",
        model="BK1600/BK1600Ultra",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        assert entry.state is ConfigEntryState.LOADED
        assert set(entry_entities(hass, entry)) == {
            "BK-SN_power_setting",
            "BK-SN_soc_setting",
            "BK-SN_state_setting",
            "BK-SN_1664",
            "BK-SN_1505",
            "BK-SN_6001",
            "BK-SN_7101",
            "BK-SN_7120",
        }
        assert {
            unique_id: state_for_unique_id(hass, entry, unique_id).state
            for unique_id in entry_entities(hass, entry)
        } == {
            "BK-SN_power_setting": "unknown",
            "BK-SN_soc_setting": "unknown",
            "BK-SN_state_setting": "Charging",
            "BK-SN_1664": "800",
            "BK-SN_1505": "2.5",
            "BK-SN_6001": "Charging",
            "BK-SN_7101": "Real-Time Control",
            "BK-SN_7120": "ON",
        }
        power_state = state_for_unique_id(hass, entry, "BK-SN_power_setting")
        assert power_state.attributes["min"] == 0
        assert power_state.attributes["max"] == 1200
        assert not any(
            registry_entry.domain == "switch"
            for registry_entry in entry_entities(hass, entry).values()
        )
        assert len(dr.async_get(hass).devices) == 1
