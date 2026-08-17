"""Runtime support shared by the closed-loop Home Assistant tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from homeassistant import loader
from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigEntries,
    ConfigEntry,
    ConfigEntryState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import frame

from custom_components.indevolt import config_flow as config_flow_module
from custom_components.indevolt import coordinator as coordinator_module
from custom_components.indevolt.const import DOMAIN

REPOSITORY_ROOT = Path(__file__).parents[2]
INTEGRATION_ROOT = REPOSITORY_ROOT / "custom_components" / DOMAIN


@dataclass
class FakeDevice:
    """One software-only device backend used by the real HA runtime."""

    data: dict[str, Any]
    config: dict[str, Any] | None = None
    config_error: Exception | None = None
    writes: list[tuple[int, list[int | float | None]]] = field(default_factory=list)
    fetches: list[list[int]] = field(default_factory=list)
    fetch_error: Exception | None = None
    write_error: Exception | None = None
    write_result: bool = True
    before_fetch: Callable[[list[int]], Awaitable[None]] | None = None
    before_write: Callable[[int, list[int | float | None]], Awaitable[None]] | None = (
        None
    )


def install_fake_devices(monkeypatch, devices: dict[str, FakeDevice]) -> None:
    """Replace only the physical HTTP boundary used by the integration."""

    class FakeAPI:
        def __init__(self, host, port, session) -> None:
            self.host = host
            self.port = port
            self.session = session
            self.device = devices[host]

        async def fetch_data(self, keys):
            requested_keys = list(keys)
            self.device.fetches.append(requested_keys)
            if self.device.before_fetch is not None:
                await self.device.before_fetch(requested_keys)
            if self.device.fetch_error is not None:
                raise self.device.fetch_error
            return {
                str(point): self.device.data[str(point)]
                for point in keys
                if str(point) in self.device.data
            }

        async def set_data(self, point, value):
            requested_value = list(value)
            self.device.writes.append((point, requested_value))
            if self.device.before_write is not None:
                await self.device.before_write(point, requested_value)
            if self.device.write_error is not None:
                raise self.device.write_error
            return self.device.write_result

        async def get_config(self):
            if self.device.config_error is not None:
                raise self.device.config_error
            if self.device.config is None:
                raise RuntimeError("Sys.GetConfig fixture is missing")
            return self.device.config

    fake_session = object()
    monkeypatch.setattr(coordinator_module, "IndevoltAPI", FakeAPI)
    monkeypatch.setattr(
        coordinator_module,
        "async_get_clientsession",
        lambda hass: fake_session,
    )
    monkeypatch.setattr(config_flow_module, "IndevoltAPI", FakeAPI)
    monkeypatch.setattr(
        config_flow_module,
        "async_get_clientsession",
        lambda hass: fake_session,
    )


@asynccontextmanager
async def home_assistant_runtime(
    tmp_path: Path,
    *,
    restore: bool = False,
    writable_storage: bool = False,
) -> AsyncIterator[HomeAssistant]:
    """Start the minimum real HA runtime needed to load the integration.

    When ``restore`` is true, Home Assistant loads the config entry, entity registry,
    and device registry stores written by an earlier runtime using the same path.
    Other tests keep HA's read-only empty registries unless ``writable_storage`` is
    requested, avoiding unnecessary filesystem writes outside persistence scenarios.
    """
    custom_components = tmp_path / "custom_components"
    custom_components.mkdir(exist_ok=True)
    integration_link = custom_components / DOMAIN
    if not integration_link.exists():
        integration_link.symlink_to(INTEGRATION_ROOT, target_is_directory=True)

    hass = HomeAssistant(str(tmp_path))
    loader.async_setup(hass)
    frame.async_setup(hass)
    dr.async_setup(hass)
    hass.config_entries = ConfigEntries(hass, {})
    use_storage = restore or writable_storage
    if use_storage:
        await hass.config_entries.async_initialize()
    await dr.async_get(hass).async_load(load_empty=not use_storage)
    await er.async_get(hass).async_load(load_empty=not use_storage)
    await hass.async_start()

    if restore:
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is ConfigEntryState.NOT_LOADED:
                await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    try:
        yield hass
    finally:
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.state is ConfigEntryState.LOADED:
                await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        await hass.async_stop(force=True)


def make_entry(
    *,
    host: str,
    serial: str,
    model: str,
    firmware: str = "1.2.3",
) -> ConfigEntry:
    """Create the same version-1 entry currently stored by Config Flow."""
    return ConfigEntry(
        data={
            "host": host,
            "port": 8080,
            "scan_interval": 30,
            "sn": serial,
            "device_model": model,
            "fw_version": firmware,
        },
        discovery_keys={},
        domain=DOMAIN,
        minor_version=1,
        options={},
        pref_disable_new_entities=None,
        pref_disable_polling=None,
        source=SOURCE_USER,
        subentries_data=(),
        title=f"INDEVOLT {model} ({host})",
        unique_id=serial,
        version=1,
    )


async def add_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Add an entry through the real ConfigEntries manager and finish setup."""
    await hass.config_entries.async_add(entry)
    await hass.async_block_till_done()


def entry_entities(hass: HomeAssistant, entry: ConfigEntry):
    """Return actual registry entries owned by one config entry."""
    return {
        item.unique_id: item
        for item in er.async_get(hass).entities.values()
        if item.platform == DOMAIN and item.config_entry_id == entry.entry_id
    }


def state_for_unique_id(hass: HomeAssistant, entry: ConfigEntry, unique_id: str):
    """Resolve a state through the actual entity registry."""
    registry_entry = entry_entities(hass, entry)[unique_id]
    return hass.states.get(registry_entry.entity_id)


def device_for_serial(hass: HomeAssistant, serial: str):
    return dr.async_get(hass).async_get_device(identifiers={(DOMAIN, serial)})


async def configure_user_flow(
    hass: HomeAssistant,
    *,
    host: str,
    scan_interval: int | None = None,
):
    form = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert form["type"] == "form"
    user_input = {"host": host}
    if scan_interval is not None:
        user_input["scan_interval"] = scan_interval
    return await hass.config_entries.flow.async_configure(form["flow_id"], user_input)


DEFAULT_DATA = {
    "1118": 12345,
    "142": 2048,
    "6001": 1001,
    "7101": 1,
    "7171": 1,
    "2618": 1001,
    "680": 0,
    "6105": 50,
    "11009": 1000,
    "11010": 800,
    "11011": 1200,
    "9016": 51,
    "9032": "PACK-1",
}
