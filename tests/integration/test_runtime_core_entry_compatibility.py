"""Runtime compatibility contracts for Home Assistant Core config entries."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigEntry, ConfigEntryState

from custom_components.indevolt.const import (
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.indevolt.entry_config import resolve_entry_config

from ._support import (
    DEFAULT_DATA,
    FakeDevice,
    add_entry,
    device_for_serial,
    entry_entities,
    home_assistant_runtime,
    install_fake_devices,
)


def test_custom_entry_resolves_core_aliases_without_mutating_source() -> None:
    """Keep custom fields while exposing the equivalent Core identities."""
    source = {
        "host": "192.0.2.90",
        "port": 18080,
        "scan_interval": 45,
        "sn": "CUSTOM-SN",
        "device_model": "FutureModel",
        "fw_version": "1.2.3",
    }

    resolved = resolve_entry_config(source)

    assert source == {
        "host": "192.0.2.90",
        "port": 18080,
        "scan_interval": 45,
        "sn": "CUSTOM-SN",
        "device_model": "FutureModel",
        "fw_version": "1.2.3",
    }
    assert resolved == {
        **source,
        "model": "FutureModel",
        "serial_number": "CUSTOM-SN",
    }


def test_conflicting_serial_aliases_are_rejected() -> None:
    """Do not create runtime identities from contradictory serial numbers."""
    with pytest.raises(ValueError, match="Conflicting INDEVOLT serial-number fields"):
        resolve_entry_config({"sn": "CUSTOM-SN", "serial_number": "CORE-SN"})


@pytest.mark.asyncio
async def test_core_entry_loads_with_runtime_aliases_and_default_port(
    monkeypatch,
    tmp_path,
) -> None:
    """Load a Core-shaped entry without changing its persistent data."""
    backend = FakeDevice(dict(DEFAULT_DATA))
    install_fake_devices(monkeypatch, {"192.0.2.91": backend})
    entry = ConfigEntry(
        data={
            "host": "192.0.2.91",
            "model": "SF2000",
            "generation": 2,
            "serial_number": "CORE-SN",
        },
        discovery_keys={},
        domain=DOMAIN,
        minor_version=2,
        options={},
        pref_disable_new_entities=None,
        pref_disable_polling=None,
        source=SOURCE_USER,
        subentries_data=(),
        title="INDEVOLT SF2000",
        unique_id="CORE-SN",
        version=1,
    )
    original_data = dict(entry.data)

    async with home_assistant_runtime(tmp_path) as hass:
        await add_entry(hass, entry)

        assert entry.state is ConfigEntryState.LOADED
        assert dict(entry.data) == original_data
        assert entry.runtime_data.config == {
            **original_data,
            "device_model": "SolidFlex/PowerFlex2000",
            "sn": "CORE-SN",
            "port": DEFAULT_PORT,
            "scan_interval": DEFAULT_SCAN_INTERVAL,
        }
        assert entry.runtime_data.api.port == DEFAULT_PORT
        assert len(entry_entities(hass, entry)) == 15
        main_device = device_for_serial(hass, "CORE-SN")
        assert main_device is not None
        assert main_device.name == "SolidFlex/PowerFlex2000 (CORE-SN)"
        assert main_device.model == "SolidFlex/PowerFlex2000"
        assert main_device.sw_version is None
