"""Real Home Assistant restart and storage persistence contracts."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.indevolt.const import DOMAIN

from ._support import (
    DEFAULT_DATA,
    FakeDevice,
    add_entry,
    configure_user_flow,
    device_for_serial,
    entry_entities,
    home_assistant_runtime,
    install_fake_devices,
    make_entry,
    state_for_unique_id,
)


def _entity_storage_snapshot(hass, entry):
    """Return the persisted identity fields that must survive a restart."""
    return {
        unique_id: (item.id, item.entity_id, item.device_id, item.name)
        for unique_id, item in entry_entities(hass, entry).items()
    }


@pytest.mark.asyncio
async def test_user_configured_entry_and_registry_customizations_survive_restart(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(
        dict(DEFAULT_DATA),
        config={
            "device": {
                "type": "CMS-SF2000",
                "sn": "PERSISTED-SN",
                "f_ver": "3.2.1",
            }
        },
    )
    install_fake_devices(monkeypatch, {"192.0.2.100": backend})

    async with home_assistant_runtime(tmp_path, writable_storage=True) as hass:
        result = await configure_user_flow(
            hass,
            host="192.0.2.100",
            scan_interval=45,
        )
        await hass.async_block_till_done()
        assert result["type"] == "create_entry"

        entry = hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN,
            "PERSISTED-SN",
        )
        assert entry is not None
        original_entry_id = entry.entry_id
        original_entry_data = dict(entry.data)
        assert hass.config_entries.async_update_entry(
            entry,
            title="User named INDEVOLT entry",
        )
        original_entry_title = entry.title

        entity_registry = er.async_get(hass)
        power_entity = entry_entities(hass, entry)["PERSISTED-SN_142"]
        renamed_power = entity_registry.async_update_entity(
            power_entity.entity_id,
            new_entity_id="sensor.user_named_indevolt_power",
            name="User named power",
        )
        assert renamed_power.entity_id == "sensor.user_named_indevolt_power"
        grid_entity = entry_entities(hass, entry)["PERSISTED-SN_grid"]
        disabled_grid = entity_registry.async_update_entity(
            grid_entity.entity_id,
            disabled_by=er.RegistryEntryDisabler.USER,
        )
        assert disabled_grid.disabled_by is er.RegistryEntryDisabler.USER
        await hass.async_block_till_done()

        main_device = device_for_serial(hass, "PERSISTED-SN")
        battery_device = device_for_serial(hass, "battery_1_PACK-1")
        assert main_device is not None
        assert battery_device is not None
        updated_main_device = dr.async_get(hass).async_update_device(
            main_device.id,
            name_by_user="Garage power station",
        )
        assert updated_main_device is not None

        original_entities = _entity_storage_snapshot(hass, entry)
        original_main_device_id = main_device.id
        original_battery_device_id = battery_device.id

    storage = tmp_path / ".storage"
    assert (storage / "core.config_entries").is_file()
    assert (storage / "core.entity_registry").is_file()
    assert (storage / "core.device_registry").is_file()

    backend.data["142"] = 4096
    backend.data.pop("9016")
    backend.data.pop("9032")

    async with home_assistant_runtime(tmp_path, restore=True) as hass:
        restored_entry = hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN,
            "PERSISTED-SN",
        )
        assert restored_entry is not None
        assert restored_entry.entry_id == original_entry_id
        assert restored_entry.title == original_entry_title
        assert dict(restored_entry.data) == original_entry_data
        assert restored_entry.state is ConfigEntryState.LOADED
        assert _entity_storage_snapshot(hass, restored_entry) == original_entities

        restored_power = entry_entities(hass, restored_entry)["PERSISTED-SN_142"]
        assert restored_power.entity_id == "sensor.user_named_indevolt_power"
        assert restored_power.name == "User named power"
        assert hass.states.get(restored_power.entity_id).state == "4096"
        restored_grid = entry_entities(hass, restored_entry)["PERSISTED-SN_grid"]
        assert restored_grid.disabled_by is er.RegistryEntryDisabler.USER
        assert hass.states.get(restored_grid.entity_id) is None

        restored_main_device = device_for_serial(hass, "PERSISTED-SN")
        restored_battery_device = device_for_serial(hass, "battery_1_PACK-1")
        assert restored_main_device is not None
        assert restored_battery_device is not None
        assert restored_main_device.id == original_main_device_id
        assert restored_main_device.name_by_user == "Garage power station"
        assert restored_battery_device.id == original_battery_device_id
        assert restored_battery_device.via_device_id == original_main_device_id
        battery_state = state_for_unique_id(
            hass,
            restored_entry,
            "PERSISTED-SN_battery_1_9016",
        )
        assert battery_state.state == "unavailable"
        assert len(entry_entities(hass, restored_entry)) == 16
        assert len(dr.async_get(hass).devices) == 2


@pytest.mark.asyncio
async def test_two_entries_restore_without_crossing_or_duplicating_state(
    monkeypatch,
    tmp_path,
) -> None:
    first = FakeDevice({**DEFAULT_DATA, "142": 1111, "9032": "FIRST-PACK"})
    second = FakeDevice({**DEFAULT_DATA, "142": 2222, "9032": "SECOND-PACK"})
    install_fake_devices(
        monkeypatch,
        {"192.0.2.101": first, "192.0.2.102": second},
    )
    first_entry = make_entry(
        host="192.0.2.101",
        serial="RESTART-FIRST-SN",
        model="SolidFlex/PowerFlex2000",
    )
    second_entry = make_entry(
        host="192.0.2.102",
        serial="RESTART-SECOND-SN",
        model="FutureModel",
    )

    async with home_assistant_runtime(tmp_path, writable_storage=True) as hass:
        await add_entry(hass, first_entry)
        await add_entry(hass, second_entry)
        original_entry_ids = {first_entry.entry_id, second_entry.entry_id}
        original_entities = {
            first_entry.unique_id: _entity_storage_snapshot(hass, first_entry),
            second_entry.unique_id: _entity_storage_snapshot(hass, second_entry),
        }
        original_device_ids = set(dr.async_get(hass).devices)

    first.data["142"] = 3333
    second.data["142"] = 4444

    async with home_assistant_runtime(tmp_path, restore=True) as hass:
        restored_entries = {
            entry.unique_id: entry
            for entry in hass.config_entries.async_entries(DOMAIN)
        }
        assert set(restored_entries) == {
            "RESTART-FIRST-SN",
            "RESTART-SECOND-SN",
        }
        assert {entry.entry_id for entry in restored_entries.values()} == (
            original_entry_ids
        )
        assert all(
            entry.state is ConfigEntryState.LOADED
            for entry in restored_entries.values()
        )
        assert {
            unique_id: _entity_storage_snapshot(hass, entry)
            for unique_id, entry in restored_entries.items()
        } == original_entities
        assert set(dr.async_get(hass).devices) == original_device_ids
        assert len(er.async_get(hass).entities) == 32
        assert len(dr.async_get(hass).devices) == 4
        assert (
            state_for_unique_id(
                hass,
                restored_entries["RESTART-FIRST-SN"],
                "RESTART-FIRST-SN_142",
            ).state
            == "3333"
        )
        assert (
            state_for_unique_id(
                hass,
                restored_entries["RESTART-SECOND-SN"],
                "RESTART-SECOND-SN_142",
            ).state
            == "4444"
        )

        first_power_entity = entry_entities(
            hass,
            restored_entries["RESTART-FIRST-SN"],
        )["RESTART-FIRST-SN_power_setting"]
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": first_power_entity.entity_id, "value": 1777},
            blocking=True,
        )
        assert first.writes == [(47016, [1777.0])]
        assert second.writes == []


@pytest.mark.asyncio
async def test_restart_retry_preserves_registries_and_recovers_without_duplicates(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.103": backend})
    entry = make_entry(
        host="192.0.2.103",
        serial="RESTART-RETRY-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path, writable_storage=True) as hass:
        await add_entry(hass, entry)
        original_entities = _entity_storage_snapshot(hass, entry)
        original_device_ids = set(dr.async_get(hass).devices)

    backend.fetch_error = TimeoutError("device temporarily offline")

    async with home_assistant_runtime(tmp_path, restore=True) as hass:
        restored_entry = hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN,
            "RESTART-RETRY-SN",
        )
        assert restored_entry is not None
        assert restored_entry.state is ConfigEntryState.SETUP_RETRY
        assert _entity_storage_snapshot(hass, restored_entry) == original_entities
        assert set(dr.async_get(hass).devices) == original_device_ids
        assert all(
            hass.states.get(item.entity_id).state == "unavailable"
            for item in entry_entities(hass, restored_entry).values()
        )

        restored_entry.async_cancel_retry_setup()
        backend.fetch_error = None
        await restored_entry.async_setup_locked(hass)
        await hass.async_block_till_done()

        assert restored_entry.state is ConfigEntryState.LOADED
        assert _entity_storage_snapshot(hass, restored_entry) == original_entities
        assert set(dr.async_get(hass).devices) == original_device_ids
        assert len(entry_entities(hass, restored_entry)) == 16
        assert len(dr.async_get(hass).devices) == 2
        assert (
            state_for_unique_id(
                hass,
                restored_entry,
                "RESTART-RETRY-SN_142",
            ).state
            == "2048"
        )
