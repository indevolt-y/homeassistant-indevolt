"""Real Home Assistant state-update and recovery contract."""

from __future__ import annotations

import pytest

from ._support import (
    DEFAULT_DATA,
    FakeDevice,
    add_entry,
    home_assistant_runtime,
    install_fake_devices,
    make_entry,
    state_for_unique_id,
)


@pytest.mark.asyncio
async def test_coordinator_updates_unavailability_and_recovery_reach_ha_states(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.30": backend})
    entry = make_entry(
        host="192.0.2.30",
        serial="UPDATE-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        coordinator = entry.runtime_data

        backend.data.update(
            {
                "142": 4096,
                "7101": 5,
                "7171": 0,
                "6105": 80,
                "9016": 75,
            }
        )
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert state_for_unique_id(hass, entry, "UPDATE-SN_142").state == "4096"
        assert (
            state_for_unique_id(hass, entry, "UPDATE-SN_work_mode").state
            == "Charge/Discharge Schedule"
        )
        assert state_for_unique_id(hass, entry, "UPDATE-SN_light").state == "off"
        assert state_for_unique_id(hass, entry, "UPDATE-SN_backup_soc").state == "80"
        assert (
            state_for_unique_id(hass, entry, "UPDATE-SN_battery_1_9016").state == "75"
        )

        backend.fetch_error = RuntimeError("polling failed")
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert coordinator.last_update_success is False
        assert state_for_unique_id(hass, entry, "UPDATE-SN_142").state == "unavailable"
        assert (
            state_for_unique_id(hass, entry, "UPDATE-SN_backup_soc").state
            == "unavailable"
        )
        assert (
            state_for_unique_id(hass, entry, "UPDATE-SN_battery_1_9016").state == "75"
        )

        backend.fetch_error = None
        backend.data["142"] = 8192
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert coordinator.last_update_success is True
        assert state_for_unique_id(hass, entry, "UPDATE-SN_142").state == "8192"
