"""Platform fallback for a model that matches no known family."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.indevolt import number as number_platform
from custom_components.indevolt import select as select_platform
from custom_components.indevolt import sensor as sensor_platform
from custom_components.indevolt import switch as switch_platform

MODEL = "FutureModel"


class FakeCoordinator:
    def __init__(self) -> None:
        self.config_entry = SimpleNamespace(
            unique_id="future-model-entry",
            data={"device_model": MODEL},
        )
        self.data = {
            "142": 2_048,
            "1505": 999,
            "9016": 51,
            "9035": 52,
            "9054": 53,
            "9149": 54,
            "9202": 55,
            "7171": 1,
        }


@pytest.mark.asyncio
async def test_unmatched_model_registers_the_gen2_fallback_contract(
    monkeypatch,
) -> None:
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

    assert set(sensor_added) == {
        ("main", "142"),
        ("battery", 1, "9016"),
        ("battery", 2, "9035"),
        ("battery", 3, "9054"),
        ("battery", 4, "9149"),
        ("battery", 5, "9202"),
        ("capability", "1505"),
    }
    assert set(number_added) == {
        "backup_soc",
        "inverter_input_limit",
        "max_output_power",
        "feed_in_power_limit",
        "power_setting",
        "soc_setting",
    }
    assert set(select_added) == {
        "work_mode",
        "state_setting",
        "load_setting",
        "led_light_strip_mode",
    }
    assert switch_added == ["light"]
