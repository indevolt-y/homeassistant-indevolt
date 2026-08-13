"""Regression tests for config-entry setup."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components import indevolt
from custom_components.indevolt.const import DOMAIN, PLATFORMS


class FakeConfigEntries:
    """Record platform forwarding calls."""

    def __init__(self) -> None:
        self.forwarded = []

    async def async_forward_entry_setups(self, entry, platforms) -> None:
        self.forwarded.append((entry, list(platforms)))


class FakeCoordinator:
    """Expose the first-refresh behavior used during entry setup."""

    instances = []
    refresh_error: Exception | None = None
    partial_entry_id: str | None = None

    def __init__(self, hass, config) -> None:
        self.hass = hass
        self.config = config
        self.first_refreshes = 0
        type(self).instances.append(self)

    async def async_config_entry_first_refresh(self) -> None:
        self.first_refreshes += 1
        if self.partial_entry_id is not None:
            self.hass.data[DOMAIN][self.partial_entry_id] = self
        if self.refresh_error is not None:
            raise self.refresh_error


def make_hass():
    return SimpleNamespace(data={}, config_entries=FakeConfigEntries())


@pytest.mark.asyncio
async def test_entry_setup_refreshes_then_forwards_all_platforms(monkeypatch) -> None:
    FakeCoordinator.instances = []
    FakeCoordinator.refresh_error = None
    FakeCoordinator.partial_entry_id = None
    monkeypatch.setattr(indevolt, "IndevoltDeviceUpdateCoordinator", FakeCoordinator)
    hass = make_hass()
    entry = SimpleNamespace(
        entry_id="entry-1",
        data={"host": "192.0.2.40", "port": 8080},
    )

    assert await indevolt.async_setup_entry(hass, entry) is True

    coordinator = FakeCoordinator.instances[0]
    assert coordinator.first_refreshes == 1
    assert entry.runtime_data is coordinator
    assert hass.config_entries.forwarded == [(entry, list(PLATFORMS))]


@pytest.mark.asyncio
async def test_entry_setup_wraps_refresh_error_and_cleans_partial_data(
    monkeypatch,
) -> None:
    FakeCoordinator.instances = []
    FakeCoordinator.refresh_error = RuntimeError("device unavailable")
    FakeCoordinator.partial_entry_id = "entry-2"
    monkeypatch.setattr(indevolt, "IndevoltDeviceUpdateCoordinator", FakeCoordinator)
    hass = make_hass()
    entry = SimpleNamespace(
        entry_id="entry-2",
        data={"host": "192.0.2.50", "port": 8080},
    )

    with pytest.raises(ConfigEntryNotReady) as error:
        await indevolt.async_setup_entry(hass, entry)

    assert isinstance(error.value.__cause__, RuntimeError)
    assert hass.data == {DOMAIN: {}}
    assert hass.config_entries.forwarded == []


@pytest.mark.asyncio
async def test_entry_setup_wraps_platform_forwarding_error(monkeypatch) -> None:
    class FailingConfigEntries(FakeConfigEntries):
        async def async_forward_entry_setups(self, entry, platforms) -> None:
            self.forwarded.append((entry, list(platforms)))
            raise RuntimeError("platform setup failed")

    FakeCoordinator.instances = []
    FakeCoordinator.refresh_error = None
    FakeCoordinator.partial_entry_id = None
    monkeypatch.setattr(indevolt, "IndevoltDeviceUpdateCoordinator", FakeCoordinator)
    hass = SimpleNamespace(data={}, config_entries=FailingConfigEntries())
    entry = SimpleNamespace(
        entry_id="entry-5",
        data={"host": "192.0.2.51", "port": 8080},
    )

    with pytest.raises(ConfigEntryNotReady) as error:
        await indevolt.async_setup_entry(hass, entry)

    coordinator = FakeCoordinator.instances[0]
    assert isinstance(error.value.__cause__, RuntimeError)
    assert str(error.value.__cause__) == "platform setup failed"
    assert coordinator.first_refreshes == 1
    assert entry.runtime_data is coordinator
    assert hass.data == {DOMAIN: {}}
    assert hass.config_entries.forwarded == [(entry, list(PLATFORMS))]
