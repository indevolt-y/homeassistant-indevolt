"""Real Home Assistant unload and reload contracts."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState

from ._support import (
    DEFAULT_DATA,
    FakeDevice,
    add_entry,
    entry_entities,
    home_assistant_runtime,
    install_fake_devices,
    make_entry,
)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Existing unload reads hass.data[DOMAIN][entry_id], but setup stores the "
        "coordinator only in entry.runtime_data"
    ),
)
@pytest.mark.asyncio
async def test_real_unload_removes_states_and_finishes_cleanly(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.70": backend})
    entry = make_entry(
        host="192.0.2.70",
        serial="UNLOAD-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        owned_entity_ids = {
            item.entity_id for item in entry_entities(hass, entry).values()
        }

        assert await hass.config_entries.async_unload(entry.entry_id) is True
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.NOT_LOADED
        assert all(hass.states.get(entity_id) is None for entity_id in owned_entity_ids)


@pytest.mark.xfail(
    strict=True,
    reason="Reload is blocked by the same existing unload failure",
)
@pytest.mark.asyncio
async def test_real_reload_preserves_entry_data_and_entity_unique_ids(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.80": backend})
    entry = make_entry(
        host="192.0.2.80",
        serial="RELOAD-SN",
        model="SolidFlex/PowerFlex2000",
    )

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)
        original_data = dict(entry.data)
        original_unique_ids = set(entry_entities(hass, entry))

        assert await hass.config_entries.async_reload(entry.entry_id) is True
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED
        assert dict(entry.data) == original_data
        assert set(entry_entities(hass, entry)) == original_unique_ids
