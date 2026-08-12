"""SolidFlex2000 config-flow contract."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.indevolt import config_flow
from custom_components.indevolt.const import DEFAULT_PORT


class FakeAPI:
    async def get_config(self):
        return {
            "device": {
                "type": "SF2000",
                "sn": "SOLIDFLEX2000-SN",
                "f_ver": "1.2.3",
            }
        }


@pytest.mark.asyncio
async def test_solidflex2000_creates_its_model_entry(monkeypatch) -> None:
    flow = config_flow.IndevoltConfigFlow()
    flow.hass = SimpleNamespace()
    unique_ids = []
    duplicate_checks = []
    api_arguments = []

    async def async_set_unique_id(unique_id):
        unique_ids.append(unique_id)

    def api_factory(host, port, session):
        api_arguments.append((host, port, session))
        return FakeAPI()

    monkeypatch.setattr(flow, "async_set_unique_id", async_set_unique_id)
    monkeypatch.setattr(
        flow,
        "_abort_if_unique_id_configured",
        lambda: duplicate_checks.append(True),
    )
    monkeypatch.setattr(
        flow,
        "async_create_entry",
        lambda **kwargs: {"type": "create_entry", **kwargs},
    )
    monkeypatch.setattr(config_flow, "IndevoltAPI", api_factory)
    monkeypatch.setattr(
        config_flow,
        "async_get_clientsession",
        lambda hass: "fake-session",
    )

    result = await flow.async_step_user(
        {"host": "192.0.2.23", "scan_interval": 45}
    )

    assert result == {
        "type": "create_entry",
        "title": "INDEVOLT SolidFlex/PowerFlex2000 (192.0.2.23)",
        "data": {
            "host": "192.0.2.23",
            "port": DEFAULT_PORT,
            "scan_interval": 45,
            "sn": "SOLIDFLEX2000-SN",
            "device_model": "SolidFlex/PowerFlex2000",
            "fw_version": "1.2.3",
        },
    }
    assert unique_ids == ["SOLIDFLEX2000-SN"]
    assert duplicate_checks == [True]
    assert api_arguments == [("192.0.2.23", DEFAULT_PORT, "fake-session")]
