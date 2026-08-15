"""BK1600 Home Assistant platform-registration contract."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.indevolt import number as number_platform
from custom_components.indevolt import select as select_platform
from custom_components.indevolt import sensor as sensor_platform
from custom_components.indevolt import switch as switch_platform

MODEL = "BK1600/BK1600Ultra"


class FakeCoordinator:
    def __init__(self) -> None:
        self.config_entry = SimpleNamespace(
            unique_id="bk1600-entry",
            data={"device_model": MODEL},
        )
        self.data = {"1664": 800, "142": 2_048, "7171": 1}


@pytest.mark.asyncio
async def test_bk1600_registers_its_own_platform_contract(monkeypatch) -> None:
    coordinator = FakeCoordinator()
    entry = SimpleNamespace(data={"device_model": MODEL}, runtime_data=coordinator)
    sensor_added = []
    number_added = []
    select_added = []
    switch_added = []
    monkeypatch.setattr(
        sensor_platform,
        "IndevoltSensorEntity",
        lambda coordinator, description: ("main", description.key),
    )
    monkeypatch.setattr(
        sensor_platform,
        "IndevoltBatterySensorEntity",
        lambda coordinator, description, pack_id: (
            "battery",
            pack_id,
            description.key,
        ),
    )
    monkeypatch.setattr(
        sensor_platform,
        "IndevoltCapabilitySensorEntity",
        lambda coordinator, capability: ("capability", capability.key),
    )
    monkeypatch.setattr(
        number_platform,
        "IndevoltNumberEntity",
        lambda coordinator, description: description.key,
    )
    monkeypatch.setattr(
        select_platform,
        "IndevoltSelectEntity",
        lambda coordinator, description: description.key,
    )
    monkeypatch.setattr(
        switch_platform,
        "IndevoltSwitchEntity",
        lambda coordinator, description: description.key,
    )

    await sensor_platform.async_setup_entry(
        None, entry, lambda entities: sensor_added.extend(entities)
    )
    await number_platform.async_setup_entry(
        None, entry, lambda entities: number_added.extend(entities)
    )
    await select_platform.async_setup_entry(
        None, entry, lambda entities: select_added.extend(entities)
    )
    await switch_platform.async_setup_entry(
        None, entry, lambda entities: switch_added.extend(entities)
    )

    assert sensor_added == [("main", "1664"), ("capability", "142")]
    assert set(number_added) == {"power_setting", "soc_setting"}
    assert select_added == ["state_setting"]
    assert switch_added == []
