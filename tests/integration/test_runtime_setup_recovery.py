"""Real Home Assistant first-setup failure and recovery contract."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr

from custom_components.indevolt.const import DOMAIN

from ._support import (
    DEFAULT_DATA,
    FakeDevice,
    add_entry,
    entry_entities,
    home_assistant_runtime,
    install_fake_devices,
    make_entry,
)


@pytest.mark.asyncio
async def test_failed_first_refresh_retries_without_mutating_entry(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(
        dict(DEFAULT_DATA),
        fetch_error=RuntimeError("temporarily unavailable"),
    )
    install_fake_devices(monkeypatch, {"192.0.2.64": backend})
    entry = make_entry(
        host="192.0.2.64",
        serial="RETRY-SN",
        model="SolidFlex/PowerFlex2000",
    )
    original_data = dict(entry.data)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        assert entry.state is ConfigEntryState.SETUP_RETRY
        assert dict(entry.data) == original_data
        assert entry_entities(hass, entry) == {}
        assert (
            dr.async_get(hass).async_get_device(identifiers={(DOMAIN, "RETRY-SN")})
            is None
        )

        entry.async_cancel_retry_setup()
        backend.fetch_error = None
        await entry.async_setup_locked(hass)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED
        assert dict(entry.data) == original_data
        assert len(entry_entities(hass, entry)) == 15
        assert (
            dr.async_get(hass).async_get_device(identifiers={(DOMAIN, "RETRY-SN")})
            is not None
        )
