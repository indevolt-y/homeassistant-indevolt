"""Real Home Assistant Config Flow contracts."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState

from custom_components.indevolt.const import DOMAIN

from ._support import (
    DEFAULT_DATA,
    FakeDevice,
    configure_user_flow,
    entry_entities,
    home_assistant_runtime,
    install_fake_devices,
)


@pytest.mark.asyncio
async def test_real_config_flow_creates_and_loads_entry(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(
        dict(DEFAULT_DATA),
        config={
            "device": {
                "type": "CMS-SF2000",
                "sn": "FLOW-SN",
                "f_ver": "3.2.1",
            }
        },
    )
    install_fake_devices(monkeypatch, {"192.0.2.60": backend})

    async with home_assistant_runtime(tmp_path) as hass:
        result = await configure_user_flow(
            hass,
            host="192.0.2.60",
            scan_interval=45,
        )
        await hass.async_block_till_done()

        assert result["type"] == "create_entry"
        assert result["title"] == ("INDEVOLT SolidFlex/PowerFlex2000 (192.0.2.60)")
        assert result["data"] == {
            "host": "192.0.2.60",
            "port": 8080,
            "scan_interval": 45,
            "sn": "FLOW-SN",
            "device_model": "SolidFlex/PowerFlex2000",
            "fw_version": "3.2.1",
        }
        created_entry = hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN,
            "FLOW-SN",
        )
        assert created_entry is not None
        assert created_entry.state is ConfigEntryState.LOADED
        assert len(entry_entities(hass, created_entry)) == 15


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Config Flow catches Home Assistant's AbortFlow in its generic Exception "
        "handler and returns unknown instead of already_configured"
    ),
)
@pytest.mark.asyncio
async def test_real_config_flow_blocks_duplicate_serial(
    monkeypatch,
    tmp_path,
) -> None:
    backend = FakeDevice(
        dict(DEFAULT_DATA),
        config={
            "device": {
                "type": "CMS-SF2000",
                "sn": "DUPLICATE-SN",
                "f_ver": "3.2.1",
            }
        },
    )
    install_fake_devices(monkeypatch, {"192.0.2.61": backend})

    async with home_assistant_runtime(tmp_path) as hass:
        created = await configure_user_flow(
            hass,
            host="192.0.2.61",
            scan_interval=45,
        )
        await hass.async_block_till_done()
        assert created["type"] == "create_entry"

        duplicate = await configure_user_flow(
            hass,
            host="192.0.2.61",
            scan_interval=30,
        )

        assert duplicate["type"] == "abort"
        assert duplicate["reason"] == "already_configured"
