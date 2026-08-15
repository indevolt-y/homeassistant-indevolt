"""Real Home Assistant multi-entry and registry isolation contracts."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr

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
async def test_two_entries_keep_entities_states_updates_and_writes_isolated(
    monkeypatch,
    tmp_path,
) -> None:
    first_data = {**DEFAULT_DATA, "142": 1111, "9032": "FIRST-PACK"}
    second_data = {**DEFAULT_DATA, "142": 2222, "9032": "SECOND-PACK"}
    first = FakeDevice(first_data)
    second = FakeDevice(second_data)
    install_fake_devices(
        monkeypatch,
        {"192.0.2.90": first, "192.0.2.91": second},
    )
    first_entry = make_entry(
        host="192.0.2.90",
        serial="ISOLATED-FIRST-SN",
        model="SolidFlex/PowerFlex2000",
    )
    second_entry = make_entry(
        host="192.0.2.91",
        serial="ISOLATED-SECOND-SN",
        model="FutureModel",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, first_entry)
        await add_entry(hass, second_entry)

        first_entities = entry_entities(hass, first_entry)
        second_entities = entry_entities(hass, second_entry)
        assert len(first_entities) == 16
        assert len(second_entities) == 16
        assert set(first_entities).isdisjoint(second_entities)
        assert {item.entity_id for item in first_entities.values()}.isdisjoint(
            item.entity_id for item in second_entities.values()
        )
        assert (
            state_for_unique_id(
                hass,
                first_entry,
                "ISOLATED-FIRST-SN_142",
            ).state
            == "1111"
        )
        assert (
            state_for_unique_id(
                hass,
                second_entry,
                "ISOLATED-SECOND-SN_142",
            ).state
            == "2222"
        )

        first.data["142"] = 3333
        await first_entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

        assert (
            state_for_unique_id(
                hass,
                first_entry,
                "ISOLATED-FIRST-SN_142",
            ).state
            == "3333"
        )
        assert (
            state_for_unique_id(
                hass,
                second_entry,
                "ISOLATED-SECOND-SN_142",
            ).state
            == "2222"
        )

        await hass.services.async_call(
            "number",
            "set_value",
            {
                "entity_id": first_entities[
                    "ISOLATED-FIRST-SN_power_setting"
                ].entity_id,
                "value": 1200,
            },
            blocking=True,
        )

        assert first.writes == [(47016, [1200.0])]
        assert second.writes == []
        assert device_for_serial(hass, "ISOLATED-FIRST-SN") is not None
        assert device_for_serial(hass, "ISOLATED-SECOND-SN") is not None
        assert device_for_serial(hass, "battery_1_FIRST-PACK") is not None
        assert device_for_serial(hass, "battery_1_SECOND-PACK") is not None


@pytest.mark.asyncio
async def test_all_five_battery_packs_register_under_their_main_device(
    monkeypatch,
    tmp_path,
) -> None:
    pack_cases = {
        1: ("9032", "9016"),
        2: ("9051", "9035"),
        3: ("9070", "9054"),
        4: ("9165", "9149"),
        5: ("9218", "9202"),
    }
    data = {"142": 2048}
    for pack_id, (serial_point, soc_point) in pack_cases.items():
        data[serial_point] = f"PACK-{pack_id}-SN"
        data[soc_point] = 50 + pack_id
    backend = FakeDevice(data)
    install_fake_devices(monkeypatch, {"192.0.2.92": backend})
    entry = make_entry(
        host="192.0.2.92",
        serial="PACK-HUB-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        main_device = device_for_serial(hass, "PACK-HUB-SN")
        assert main_device is not None

        for pack_id, (_serial_point, soc_point) in pack_cases.items():
            battery_device = device_for_serial(
                hass,
                f"battery_{pack_id}_PACK-{pack_id}-SN",
            )
            assert battery_device is not None
            assert battery_device.via_device_id == main_device.id
            registry_entry = entry_entities(hass, entry)[
                f"PACK-HUB-SN_battery_{pack_id}_{soc_point}"
            ]
            assert registry_entry.device_id == battery_device.id
            assert hass.states.get(registry_entry.entity_id).state == str(50 + pack_id)

        assert len(dr.async_get(hass).devices) == 6


@pytest.mark.asyncio
async def test_entities_missing_on_first_response_are_not_added_later(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice({"142": 2048})
    install_fake_devices(monkeypatch, {"192.0.2.93": backend})
    entry = make_entry(
        host="192.0.2.93",
        serial="FIRST-RESPONSE-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        initial_entities = entry_entities(hass, entry)
        assert "FIRST-RESPONSE-SN_142" in initial_entities
        assert "FIRST-RESPONSE-SN_1118" not in initial_entities
        assert "FIRST-RESPONSE-SN_light" not in initial_entities
        assert "FIRST-RESPONSE-SN_battery_1_9016" not in initial_entities

        backend.data = {
            "1118": 12345,
            "7171": 1,
            "9016": 75,
            "9032": "LATE-PACK",
        }
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

        later_entities = entry_entities(hass, entry)
        assert set(later_entities) == set(initial_entities)
        assert (
            state_for_unique_id(
                hass,
                entry,
                "FIRST-RESPONSE-SN_142",
            ).state
            == "unknown"
        )
        assert device_for_serial(hass, "battery_1_LATE-PACK") is None


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Existing unload reads hass.data[DOMAIN][entry_id], so Home Assistant "
        "cannot complete the isolation check until that lifecycle bug is fixed"
    ),
)
@pytest.mark.asyncio
async def test_unloading_one_entry_leaves_the_other_entry_running(
    monkeypatch,
    tmp_path,
) -> None:
    first = FakeDevice({**DEFAULT_DATA, "9032": "UNLOAD-FIRST-PACK"})
    second = FakeDevice({**DEFAULT_DATA, "9032": "UNLOAD-SECOND-PACK"})
    install_fake_devices(
        monkeypatch,
        {"192.0.2.94": first, "192.0.2.95": second},
    )
    first_entry = make_entry(
        host="192.0.2.94",
        serial="UNLOAD-FIRST-SN",
        model="SolidFlex/PowerFlex2000",
    )
    second_entry = make_entry(
        host="192.0.2.95",
        serial="UNLOAD-SECOND-SN",
        model="FutureModel",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, first_entry)
        await add_entry(hass, second_entry)
        second_entity_ids = {
            item.entity_id for item in entry_entities(hass, second_entry).values()
        }

        assert await hass.config_entries.async_unload(first_entry.entry_id) is True
        await hass.async_block_till_done()

        assert first_entry.state is ConfigEntryState.NOT_LOADED
        assert second_entry.state is ConfigEntryState.LOADED
        assert all(
            hass.states.get(entity_id) is not None for entity_id in second_entity_ids
        )
        second.data["142"] = 9999
        await second_entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        assert (
            state_for_unique_id(
                hass,
                second_entry,
                "UNLOAD-SECOND-SN_142",
            ).state
            == "9999"
        )
