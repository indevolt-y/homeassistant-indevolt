"""Regression tests for coordinator construction and batching helpers."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.indevolt import coordinator as coordinator_module
from custom_components.indevolt.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from custom_components.indevolt.coordinator import (
    IndevoltDeviceUpdateCoordinator,
    _chunked,
)


@pytest.mark.parametrize(
    ("extra_config", "expected_seconds"),
    [({}, DEFAULT_SCAN_INTERVAL), ({"scan_interval": 45}, 45)],
)
def test_coordinator_constructor_keeps_connection_and_interval_contract(
    monkeypatch,
    extra_config,
    expected_seconds,
) -> None:
    hass = object()
    config = {
        "host": "192.0.2.40",
        "port": 8080,
        "device_model": "FutureModel",
        **extra_config,
    }
    super_arguments = []
    session_calls = []
    api_arguments = []

    def fake_super_init(self, received_hass, logger, **kwargs) -> None:
        self.hass = received_hass
        super_arguments.append((received_hass, logger, kwargs))

    def fake_get_clientsession(received_hass):
        assert received_hass is hass
        session = f"session-{len(session_calls) + 1}"
        session_calls.append(session)
        return session

    def fake_api(*, host, port, session):
        api_arguments.append((host, port, session))
        return "api-client"

    monkeypatch.setattr(DataUpdateCoordinator, "__init__", fake_super_init)
    monkeypatch.setattr(
        coordinator_module,
        "async_get_clientsession",
        fake_get_clientsession,
    )
    monkeypatch.setattr(coordinator_module, "IndevoltAPI", fake_api)

    coordinator = IndevoltDeviceUpdateCoordinator(hass, config)

    assert coordinator.config is config
    assert coordinator.session == "session-1"
    assert coordinator.api == "api-client"
    assert session_calls == ["session-1", "session-2"]
    assert api_arguments == [("192.0.2.40", 8080, "session-2")]
    assert len(super_arguments) == 1
    received_hass, _logger, kwargs = super_arguments[0]
    assert received_hass is hass
    assert kwargs == {
        "name": DOMAIN,
        "update_interval": timedelta(seconds=expected_seconds),
    }


@pytest.mark.parametrize(
    ("values", "size", "expected"),
    [
        ([], 8, []),
        ([1], 8, [[1]]),
        (list(range(8)), 8, [list(range(8))]),
        (list(range(9)), 8, [list(range(8)), [8]]),
        (list(range(5)), 2, [[0, 1], [2, 3], [4]]),
    ],
)
def test_chunked_preserves_order_and_tail(values, size, expected) -> None:
    assert list(_chunked(values, size)) == expected
