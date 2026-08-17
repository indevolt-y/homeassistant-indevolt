"""Regression tests for config-entry unload."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components import indevolt
from custom_components.indevolt.const import DOMAIN, PLATFORMS


class FakeConfigEntries:
    """Return and record a fixed platform-unload result."""

    def __init__(self, unload_result: bool, loaded_entries=None) -> None:
        self.unload_result = unload_result
        self.loaded_entries = list(loaded_entries or [])
        self.unloaded = []

    async def async_unload_platforms(self, entry, platforms) -> bool:
        self.unloaded.append((entry, list(platforms)))
        return self.unload_result

    def async_loaded_entries(self, domain):
        assert domain == DOMAIN
        return self.loaded_entries


class FakeCoordinator:
    """Record coordinator shutdown calls."""

    def __init__(self) -> None:
        self.shutdowns = 0

    async def async_shutdown(self) -> None:
        self.shutdowns += 1


def make_hass(*, unload_result: bool, loaded_entries=None):
    return SimpleNamespace(
        data={DOMAIN: {}},
        config_entries=FakeConfigEntries(unload_result, loaded_entries),
    )


@pytest.mark.asyncio
async def test_successful_unload_shuts_down_and_removes_last_domain_entry() -> None:
    coordinator = FakeCoordinator()
    entry = SimpleNamespace(entry_id="entry-3", runtime_data=coordinator)
    hass = make_hass(unload_result=True)

    assert await indevolt.async_unload_entry(hass, entry) is True

    assert coordinator.shutdowns == 1
    assert hass.config_entries.unloaded == [(entry, list(PLATFORMS))]
    assert DOMAIN not in hass.data


@pytest.mark.asyncio
async def test_failed_platform_unload_keeps_coordinator_running() -> None:
    coordinator = FakeCoordinator()
    entry = SimpleNamespace(entry_id="entry-4", runtime_data=coordinator)
    hass = make_hass(unload_result=False)

    assert await indevolt.async_unload_entry(hass, entry) is False

    assert coordinator.shutdowns == 0
    assert hass.config_entries.unloaded == [(entry, list(PLATFORMS))]
    assert hass.data == {DOMAIN: {}}


@pytest.mark.asyncio
async def test_successful_unload_preserves_other_runtime_coordinators() -> None:
    coordinator = FakeCoordinator()
    other_coordinator = FakeCoordinator()
    entry = SimpleNamespace(entry_id="entry-6", runtime_data=coordinator)
    other_entry = SimpleNamespace(entry_id="entry-7", runtime_data=other_coordinator)
    hass = make_hass(unload_result=True, loaded_entries=[other_entry])

    assert await indevolt.async_unload_entry(hass, entry) is True

    assert coordinator.shutdowns == 1
    assert other_entry.runtime_data.shutdowns == 0
    assert hass.data == {DOMAIN: {}}
