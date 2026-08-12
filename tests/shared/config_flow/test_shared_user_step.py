"""Regression tests for config-flow behavior before a model is identified."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from custom_components.indevolt import config_flow
from custom_components.indevolt.const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL


class FakeAPI:
    """Return or fail before a device model is available."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    async def get_config(self):
        if self.error is not None:
            raise self.error
        return None


def make_flow(monkeypatch, api: FakeAPI):
    """Build a config flow whose pre-model effects are observable."""
    flow = config_flow.IndevoltConfigFlow()
    flow.hass = SimpleNamespace()
    unique_ids = []
    duplicate_checks = []
    api_arguments = []

    async def async_set_unique_id(unique_id):
        unique_ids.append(unique_id)

    def api_factory(host, port, session):
        api_arguments.append((host, port, session))
        return api

    monkeypatch.setattr(flow, "async_set_unique_id", async_set_unique_id)
    monkeypatch.setattr(
        flow,
        "_abort_if_unique_id_configured",
        lambda: duplicate_checks.append(True),
    )
    monkeypatch.setattr(
        flow,
        "async_show_form",
        lambda **kwargs: {"type": "form", **kwargs},
    )
    monkeypatch.setattr(config_flow, "IndevoltAPI", api_factory)
    monkeypatch.setattr(
        config_flow,
        "async_get_clientsession",
        lambda hass: "fake-session",
    )
    return flow, unique_ids, duplicate_checks, api_arguments


@pytest.mark.asyncio
async def test_user_step_shows_form_with_default_scan_interval(monkeypatch) -> None:
    flow, unique_ids, duplicate_checks, api_arguments = make_flow(
        monkeypatch,
        FakeAPI(),
    )

    result = await flow.async_step_user()

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    assert result["data_schema"]({"host": "192.0.2.10"}) == {
        "host": "192.0.2.10",
        "scan_interval": DEFAULT_SCAN_INTERVAL,
    }
    assert unique_ids == []
    assert duplicate_checks == []
    assert api_arguments == []


@pytest.mark.asyncio
async def test_user_step_reports_timeout_without_identifying_model(
    monkeypatch,
) -> None:
    flow, unique_ids, duplicate_checks, api_arguments = make_flow(
        monkeypatch,
        FakeAPI(error=asyncio.TimeoutError()),
    )

    result = await flow.async_step_user({"host": "192.0.2.30"})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "timeout"}
    assert unique_ids == []
    assert duplicate_checks == []
    assert api_arguments == [("192.0.2.30", DEFAULT_PORT, "fake-session")]
