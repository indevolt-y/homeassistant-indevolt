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


class PayloadAPI:
    """Return an exact Sys.GetConfig payload."""

    def __init__(self, payload) -> None:
        self.payload = payload

    async def get_config(self):
        return self.payload


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


@pytest.mark.parametrize(
    "api",
    [
        FakeAPI(error=RuntimeError("broken response")),
        PayloadAPI(None),
        PayloadAPI({}),
        PayloadAPI({"device": {"type": None}}),
    ],
    ids=["api-error", "null-payload", "missing-device", "null-model"],
)
@pytest.mark.asyncio
async def test_user_step_reports_unknown_for_existing_non_timeout_failures(
    monkeypatch,
    api,
) -> None:
    flow, unique_ids, duplicate_checks, api_arguments = make_flow(monkeypatch, api)

    result = await flow.async_step_user({"host": "192.0.2.31"})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "unknown"}
    assert unique_ids == []
    assert duplicate_checks == []
    assert api_arguments == [("192.0.2.31", DEFAULT_PORT, "fake-session")]


@pytest.mark.parametrize(
    ("reported_model", "saved_model"),
    [
        ("CMS-SF2000", "SolidFlex/PowerFlex2000"),
        ("prefix-SF2000-suffix", "SolidFlex/PowerFlex2000"),
        ("CMS-BK1600", "BK1600/BK1600Ultra"),
        ("prefix-BK1600-suffix", "BK1600/BK1600Ultra"),
        ("FutureModel", "FutureModel"),
    ],
)
@pytest.mark.asyncio
async def test_user_step_preserves_existing_substring_mapping_and_default_interval(
    monkeypatch,
    reported_model,
    saved_model,
) -> None:
    api = PayloadAPI(
        {
            "device": {
                "type": reported_model,
                "sn": "DEVICE-SN",
                "f_ver": "1.2.3",
            }
        }
    )
    flow, unique_ids, duplicate_checks, api_arguments = make_flow(monkeypatch, api)
    monkeypatch.setattr(
        flow,
        "async_create_entry",
        lambda **kwargs: {"type": "create_entry", **kwargs},
    )

    result = await flow.async_step_user({"host": "192.0.2.32"})

    assert result == {
        "type": "create_entry",
        "title": f"INDEVOLT {saved_model} (192.0.2.32)",
        "data": {
            "host": "192.0.2.32",
            "port": DEFAULT_PORT,
            "scan_interval": DEFAULT_SCAN_INTERVAL,
            "sn": "DEVICE-SN",
            "device_model": saved_model,
            "fw_version": "1.2.3",
        },
    }
    assert unique_ids == ["DEVICE-SN"]
    assert duplicate_checks == [True]
    assert api_arguments == [("192.0.2.32", DEFAULT_PORT, "fake-session")]
