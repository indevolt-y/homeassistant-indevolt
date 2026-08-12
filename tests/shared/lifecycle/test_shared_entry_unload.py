"""Regression tests for config-entry unload."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components import indevolt
from custom_components.indevolt.const import DOMAIN, PLATFORMS


class FakeConfigEntries:
    """Return and record a fixed platform-unload result."""

    def __init__(self, unload_result: bool) -> None:
        self.unload_result = unload_result
        self.unloaded = []

    async def async_unload_platforms(self, entry, platforms) -> bool:
        self.unloaded.append((entry, list(platforms)))
        return self.unload_result


class FakeCoordinator:
    """Record coordinator shutdown calls."""

    def __init__(self) -> None:
        self.shutdowns = 0

    async def async_shutdown(self) -> None:
        self.shutdowns += 1


def make_hass(entry, coordinator, *, unload_result: bool):
    return SimpleNamespace(
        data={DOMAIN: {entry.entry_id: coordinator}},
        config_entries=FakeConfigEntries(unload_result),
    )


@pytest.mark.asyncio
async def test_successful_unload_shuts_down_and_removes_last_domain_entry() -> None:
    entry = SimpleNamespace(entry_id="entry-3")
    coordinator = FakeCoordinator()
    hass = make_hass(entry, coordinator, unload_result=True)

    assert await indevolt.async_unload_entry(hass, entry) is True

    assert coordinator.shutdowns == 1
    assert hass.config_entries.unloaded == [(entry, list(PLATFORMS))]
    assert DOMAIN not in hass.data


@pytest.mark.asyncio
async def test_failed_platform_unload_keeps_coordinator_running() -> None:
    entry = SimpleNamespace(entry_id="entry-4")
    coordinator = FakeCoordinator()
    hass = make_hass(entry, coordinator, unload_result=False)

    assert await indevolt.async_unload_entry(hass, entry) is False

    assert coordinator.shutdowns == 0
    assert hass.config_entries.unloaded == [(entry, list(PLATFORMS))]
    assert hass.data == {DOMAIN: {entry.entry_id: coordinator}}
