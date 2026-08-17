"""Real Home Assistant service and target-resolution contracts."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ServiceValidationError

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
        assert len(entry_entities(hass, first_entry)) == 16
        assert len(entry_entities(hass, second_entry)) == 16


@pytest.mark.asyncio
async def test_all_number_entities_accept_real_ha_service_calls(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.41": backend})
    entry = make_entry(
        host="192.0.2.41",
        serial="NUMBER-SN",
        model="SolidFlex/PowerFlex2000",
    )
    values = {
        "backup_soc": 80,
        "inverter_input_limit": 1200,
        "max_output_power": 1800,
        "feed_in_power_limit": 900,
        "power_setting": 2400,
        "soc_setting": 75,
    }

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)

        for key, value in values.items():
            await hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": entities[f"NUMBER-SN_{key}"].entity_id,
                    "value": value,
                },
                blocking=True,
            )

        assert backend.writes == [
            (1142, [80.0]),
            (1138, [1200.0]),
            (1147, [1800.0]),
            (1146, [900.0]),
            (47016, [2400.0]),
            (47017, [75.0]),
        ]


@pytest.mark.asyncio
async def test_documented_11009_does_not_replace_the_existing_write_transport(
    monkeypatch,
    tmp_path,
) -> None:
    """Keep the 1.2 control reading 11009 and writing 1138."""
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.46": backend})
    entry = make_entry(
        host="192.0.2.46",
        serial="AC-LIMIT-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)
        number_entity = entities["AC-LIMIT-SN_inverter_input_limit"]

        assert "AC-LIMIT-SN_11009" not in entities
        state = hass.states.get(number_entity.entity_id)
        assert state is not None
        assert state.state == "1000"

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": number_entity.entity_id, "value": 1200},
            blocking=True,
        )

        assert backend.writes == [(1138, [1200.0])]
        assert all(point != 11009 for point, _value in backend.writes)


@pytest.mark.asyncio
async def test_documented_2618_does_not_replace_the_existing_write_transport(
    monkeypatch,
    tmp_path,
) -> None:
    """Keep the 1.2 switch reading 2618 and writing 1143."""
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.47": backend})
    entry = make_entry(
        host="192.0.2.47",
        serial="GRID-CHARGE-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)
        switch_entity = entities["GRID-CHARGE-SN_grid"]

        assert "GRID-CHARGE-SN_2618" not in entities
        state = hass.states.get(switch_entity.entity_id)
        assert state is not None
        assert state.state == "on"

        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": switch_entity.entity_id},
            blocking=True,
        )

        assert backend.writes == [(1143, [0])]
        assert all(point != 2618 for point, _value in backend.writes)


@pytest.mark.asyncio
async def test_documented_6505_does_not_replace_the_existing_write_transport(
    monkeypatch,
    tmp_path,
) -> None:
    """Keep the 1.2 Backup SOC reading 6105 and writing 1142."""
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.48": backend})
    entry = make_entry(
        host="192.0.2.48",
        serial="BACKUP-SOC-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)
        number_entity = entities["BACKUP-SOC-SN_backup_soc"]

        assert "BACKUP-SOC-SN_6505" not in entities
        state = hass.states.get(number_entity.entity_id)
        assert state is not None
        assert state.state == "50"
        assert state.attributes["min"] == 5
        assert state.attributes["max"] == 100

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": number_entity.entity_id, "value": 80},
            blocking=True,
        )

        assert backend.writes == [(1142, [80.0])]
        assert all(point != 6505 for point, _value in backend.writes)


@pytest.mark.asyncio
async def test_all_select_entities_accept_real_ha_service_calls(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.42": backend})
    entry = make_entry(
        host="192.0.2.42",
        serial="SELECT-SN",
        model="SolidFlex/PowerFlex2000",
    )
    options = {
        "work_mode": "Real-Time Control",
        "state_setting": "Discharging",
        "load_setting": "Custom",
    }

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)

        for key, option in options.items():
            await hass.services.async_call(
                "select",
                "select_option",
                {
                    "entity_id": entities[f"SELECT-SN_{key}"].entity_id,
                    "option": option,
                },
                blocking=True,
            )
        await hass.async_block_till_done()

        assert backend.writes == [(47005, [4]), (47015, [2]), (1, [4])]
        assert hass.states.get(entities["SELECT-SN_work_mode"].entity_id).state == (
            "Self-Consumed Prioritized"
        )
        assert (
            hass.states.get(entities["SELECT-SN_state_setting"].entity_id).state
            == "Charging"
        )
        assert hass.states.get(entities["SELECT-SN_load_setting"].entity_id).state == (
            "unknown"
        )


@pytest.mark.asyncio
async def test_all_switch_entities_accept_real_ha_service_calls(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.43": backend})
    entry = make_entry(
        host="192.0.2.43",
        serial="SWITCH-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)

        for key, service in (
            ("light", "turn_off"),
            ("grid", "turn_on"),
            ("bypass", "turn_on"),
        ):
            await hass.services.async_call(
                "switch",
                service,
                {"entity_id": entities[f"SWITCH-SN_{key}"].entity_id},
                blocking=True,
            )
        await hass.async_block_till_done()

        assert backend.writes == [(7265, [0]), (1143, [1]), (7266, [1])]
        assert hass.states.get(entities["SWITCH-SN_light"].entity_id).state == "off"
        assert hass.states.get(entities["SWITCH-SN_grid"].entity_id).state == "off"
        assert hass.states.get(entities["SWITCH-SN_bypass"].entity_id).state == "on"


@pytest.mark.asyncio
async def test_real_entity_services_reject_invalid_values_before_device_write(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.44": backend})
    entry = make_entry(
        host="192.0.2.44",
        serial="INVALID-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)

        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": entities["INVALID-SN_power_setting"].entity_id,
                    "value": 10_801,
                },
                blocking=True,
            )
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "select",
                "select_option",
                {
                    "entity_id": entities["INVALID-SN_work_mode"].entity_id,
                    "option": "Unknown Mode",
                },
                blocking=True,
            )

        assert backend.writes == []


@pytest.mark.asyncio
async def test_real_write_failures_keep_each_entity_platforms_existing_feedback(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(
        dict(DEFAULT_DATA),
        write_error=RuntimeError("device rejected write"),
    )
    install_fake_devices(monkeypatch, {"192.0.2.45": backend})
    entry = make_entry(
        host="192.0.2.45",
        serial="ERROR-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        entities = entry_entities(hass, entry)

        with pytest.raises(RuntimeError, match="^device rejected write$"):
            await hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": entities["ERROR-SN_power_setting"].entity_id,
                    "value": 1200,
                },
                blocking=True,
            )
        assert hass.states.get(entities["ERROR-SN_power_setting"].entity_id).state == (
            "unknown"
        )

        with pytest.raises(RuntimeError, match="^device rejected write$"):
            await hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": entities["ERROR-SN_light"].entity_id},
                blocking=True,
            )
        assert hass.states.get(entities["ERROR-SN_light"].entity_id).state == "off"
        assert backend.writes == [(47016, [1200.0]), (7265, [0])]


@pytest.mark.parametrize(
    "service_data",
    [
        {"mode": "Real-Time Control", "power": 1200},
        {
            "device_id": ["unused-device-id"],
            "mode": "Real-Time Control",
            "power": 10_801,
        },
    ],
    ids=["missing-target", "power-over-limit"],
)
@pytest.mark.asyncio
async def test_real_action_validation_fails_before_device_write(
    monkeypatch,
    tmp_path,
    service_data,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.46": backend})
    entry = make_entry(
        host="192.0.2.46",
        serial="ACTION-ERROR-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                "set_solidflex_powerflex_work_mode",
                service_data,
                blocking=True,
            )

        assert backend.writes == []


@pytest.mark.asyncio
async def test_real_action_stops_after_a_later_target_write_failure(
    monkeypatch,
    tmp_path,
) -> None:
    first = FakeDevice(dict(DEFAULT_DATA))
    second = FakeDevice(
        dict(DEFAULT_DATA),
        write_error=RuntimeError("second target failed"),
    )
    install_fake_devices(
        monkeypatch,
        {"192.0.2.47": first, "192.0.2.48": second},
    )
    first_entry = make_entry(
        host="192.0.2.47",
        serial="PARTIAL-FIRST-SN",
        model="SolidFlex/PowerFlex2000",
    )
    second_entry = make_entry(
        host="192.0.2.48",
        serial="PARTIAL-SECOND-SN",
        model="FutureModel",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, first_entry)
        await add_entry(hass, second_entry)
        first_device = device_for_serial(hass, "PARTIAL-FIRST-SN")
        second_device = device_for_serial(hass, "PARTIAL-SECOND-SN")
        assert first_device is not None
        assert second_device is not None

        with pytest.raises(RuntimeError, match="^second target failed$"):
            await hass.services.async_call(
                DOMAIN,
                "set_solidflex_powerflex_work_mode",
                {
                    "device_id": [first_device.id, second_device.id],
                    "mode": "Self-Consumed Prioritized",
                },
                blocking=True,
            )

        assert first.writes == [(47005, [1])]
        assert second.writes == [(47005, [1])]
