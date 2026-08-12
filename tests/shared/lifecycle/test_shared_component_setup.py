"""Regression tests for component-level setup."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components import indevolt
from custom_components.indevolt.const import DOMAIN


class FakeServices:
    """Store service registrations made by the component."""

    def __init__(self) -> None:
        self.handlers = {}

    def has_service(self, domain, service) -> bool:
        return (domain, service) in self.handlers

    def async_register(self, domain, service, handler) -> None:
        self.handlers[(domain, service)] = handler


@pytest.mark.asyncio
async def test_component_setup_registers_services_only_once() -> None:
    hass = SimpleNamespace(data={}, services=FakeServices())

    assert await indevolt.async_setup(hass, {}) is True
    assert await indevolt.async_setup(hass, {}) is True

    assert hass.data == {DOMAIN: {}}
    assert set(hass.services.handlers) == {
        (DOMAIN, "set_solidflex_powerflex_work_mode"),
        (DOMAIN, "set_bk1600_work_mode"),
    }
