"""Real Home Assistant service and target-resolution contracts."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState

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
)


@pytest.mark.asyncio
async def test_real_ha_services_reach_number_switch_and_action_writes(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.40": backend})
    entry = make_entry(
        host="192.0.2.40",
        serial="SERVICE-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        main_device = device_for_serial(hass, "SERVICE-SN")
        assert main_device is not None
        number_entity = entry_entities(hass, entry)["SERVICE-SN_power_setting"]
        switch_entity = entry_entities(hass, entry)["SERVICE-SN_light"]

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": number_entity.entity_id, "value": 1200},
            blocking=True,
        )
        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": switch_entity.entity_id},
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            "set_solidflex_powerflex_work_mode",
            {
                "device_id": [main_device.id],
                "mode": "Real-Time Control",
                "state": "Discharging",
                "power": 2400,
                "soc": 80,
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert backend.writes == [
            (47016, [1200.0]),
            (7265, [0]),
            (47005, [4]),
            (47015, [2, 2400, 80]),
        ]


@pytest.mark.asyncio
async def test_action_targets_two_real_registry_devices_in_input_order(
    monkeypatch,
    tmp_path,
) -> None:
    first = FakeDevice(dict(DEFAULT_DATA))
    second = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(
        monkeypatch,
        {
            "192.0.2.50": first,
            "192.0.2.51": second,
        },
    )
    first_entry = make_entry(
        host="192.0.2.50",
        serial="FIRST-SN",
        model="SolidFlex/PowerFlex2000",
    )
    second_entry = make_entry(
        host="192.0.2.51",
        serial="SECOND-SN",
        model="FutureModel",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, first_entry)
        await add_entry(hass, second_entry)
        first_device = device_for_serial(hass, "FIRST-SN")
        second_device = device_for_serial(hass, "SECOND-SN")
        assert first_device is not None
        assert second_device is not None

        await hass.services.async_call(
            DOMAIN,
            "set_solidflex_powerflex_work_mode",
            {
                "device_id": [second_device.id, first_device.id],
                "mode": "Self-Consumed Prioritized",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        assert second.writes == [(47005, [1])]
        assert first.writes == [(47005, [1])]
        assert first_entry.state is ConfigEntryState.LOADED
        assert second_entry.state is ConfigEntryState.LOADED
        assert len(entry_entities(hass, first_entry)) == 15
        assert len(entry_entities(hass, second_entry)) == 15
