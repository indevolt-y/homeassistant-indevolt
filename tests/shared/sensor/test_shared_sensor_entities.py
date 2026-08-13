"""Complete entity-creation and runtime contracts for sensors."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.indevolt import sensor as sensor_platform
from custom_components.indevolt.const import DOMAIN
from custom_components.indevolt.sensor import (
    IndevoltBatterySensorEntity,
    IndevoltSensorEntity,
)
from custom_components.indevolt.sensor_descriptions.battery_pack import (
    BATTERY_PACK_SENSORS,
)
from custom_components.indevolt.sensor_descriptions.gen1 import SENSORS_GEN1
from custom_components.indevolt.sensor_descriptions.gen2 import SENSORS_GEN2


class FakeCoordinator:
    """Provide the state used by all sensor paths."""

    def __init__(self, model: str, data=None) -> None:
        self.config_entry = SimpleNamespace(
            unique_id="sensor-entry",
            data={
                "sn": "MAIN-SN",
                "device_model": model,
                "fw_version": "1.2.3",
            },
        )
        self.data = dict(data or {})
        self.last_update_success = True


def _entry(coordinator: FakeCoordinator):
    return SimpleNamespace(
        data=coordinator.config_entry.data,
        runtime_data=coordinator,
    )


@pytest.mark.parametrize("model", ["BK1600/BK1600Ultra", "prefix-BK1600-suffix"])
@pytest.mark.asyncio
async def test_bk_route_creates_every_non_null_gen1_sensor_in_definition_order(
    monkeypatch,
    model,
) -> None:
    coordinator = FakeCoordinator(
        model,
        {description.key: 0 for description in SENSORS_GEN1},
    )
    added = []
    monkeypatch.setattr(
        sensor_platform,
        "IndevoltSensorEntity",
        lambda coordinator, description: description.key,
    )

    await sensor_platform.async_setup_entry(
        None,
        _entry(coordinator),
        lambda entities: added.extend(entities),
    )

    assert added == [description.key for description in SENSORS_GEN1]


@pytest.mark.parametrize("model", ["SolidFlex/PowerFlex2000", "FutureModel"])
@pytest.mark.asyncio
async def test_default_route_creates_every_non_null_main_and_battery_sensor(
    monkeypatch,
    model,
) -> None:
    all_descriptions = [
        *SENSORS_GEN2,
        *(
            description
            for descriptions in BATTERY_PACK_SENSORS.values()
            for description in descriptions
        ),
    ]
    coordinator = FakeCoordinator(
        model,
        {description.key: 0 for description in all_descriptions},
    )
    added = []
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

    await sensor_platform.async_setup_entry(
        None,
        _entry(coordinator),
        lambda entities: added.extend(entities),
    )

    assert added[: len(SENSORS_GEN2)] == [
        ("main", description.key) for description in SENSORS_GEN2
    ]
    assert set(added[len(SENSORS_GEN2) :]) == {
        ("battery", pack_id, description.key)
        for pack_id, descriptions in BATTERY_PACK_SENSORS.items()
        for description in descriptions
    }
    assert len(added) == len(SENSORS_GEN2) + 40


@pytest.mark.parametrize("value", [0, False, ""])
@pytest.mark.parametrize(
    ("model", "point"),
    [
        ("BK1600/BK1600Ultra", "1664"),
        ("SolidFlex/PowerFlex2000", "142"),
    ],
)
@pytest.mark.asyncio
async def test_zero_false_and_empty_string_still_create_sensor(
    monkeypatch,
    value,
    model,
    point,
) -> None:
    coordinator = FakeCoordinator(model, {point: value})
    added = []
    monkeypatch.setattr(
        sensor_platform,
        "IndevoltSensorEntity",
        lambda coordinator, description: description.key,
    )
    monkeypatch.setattr(
        sensor_platform,
        "IndevoltBatterySensorEntity",
        lambda coordinator, description, pack_id: description.key,
    )

    await sensor_platform.async_setup_entry(
        None,
        _entry(coordinator),
        lambda entities: added.extend(entities),
    )

    assert added == [point]


@pytest.mark.parametrize(
    "model",
    ["BK1600/BK1600Ultra", "SolidFlex/PowerFlex2000", "FutureModel"],
)
@pytest.mark.parametrize("data", [{}, {"1664": None, "142": None, "9016": None}])
@pytest.mark.asyncio
async def test_missing_and_null_points_create_no_sensor(
    monkeypatch,
    model,
    data,
) -> None:
    coordinator = FakeCoordinator(model, data)
    added = []
    monkeypatch.setattr(
        sensor_platform,
        "IndevoltSensorEntity",
        lambda coordinator, description: description.key,
    )
    monkeypatch.setattr(
        sensor_platform,
        "IndevoltBatterySensorEntity",
        lambda coordinator, description, pack_id: description.key,
    )

    await sensor_platform.async_setup_entry(
        None,
        _entry(coordinator),
        lambda entities: added.extend(entities),
    )

    assert added == []


def test_every_sensor_unique_id_keeps_legacy_point_keys() -> None:
    bk_coordinator = FakeCoordinator("BK1600/BK1600Ultra")
    default_coordinator = FakeCoordinator("SolidFlex/PowerFlex2000")

    gen1_ids = {
        IndevoltSensorEntity(bk_coordinator, description).unique_id
        for description in SENSORS_GEN1
    }
    gen2_ids = {
        IndevoltSensorEntity(default_coordinator, description).unique_id
        for description in SENSORS_GEN2
    }
    battery_ids = {
        IndevoltBatterySensorEntity(
            default_coordinator,
            description,
            pack_id,
        ).unique_id
        for pack_id, descriptions in BATTERY_PACK_SENSORS.items()
        for description in descriptions
    }

    assert gen1_ids == {
        f"sensor-entry_{description.key}" for description in SENSORS_GEN1
    }
    assert gen2_ids == {
        f"sensor-entry_{description.key}" for description in SENSORS_GEN2
    }
    assert battery_ids == {
        f"sensor-entry_battery_{pack_id}_{description.key}"
        for pack_id, descriptions in BATTERY_PACK_SENSORS.items()
        for description in descriptions
    }
    assert len(battery_ids) == 40


def test_main_sensor_reads_latest_value_and_coordinator_availability() -> None:
    description = next(item for item in SENSORS_GEN1 if item.key == "1505")
    coordinator = FakeCoordinator("BK1600/BK1600Ultra", {"1505": 1000})
    entity = IndevoltSensorEntity(coordinator, description)

    assert entity.native_value == 1
    assert entity.available is True

    coordinator.data["1505"] = 2500
    coordinator.last_update_success = False

    assert entity.native_value == 2.5
    assert entity.available is False


def test_existing_plain_sensor_returns_none_when_point_later_disappears() -> None:
    description = next(item for item in SENSORS_GEN2 if item.key == "142")
    coordinator = FakeCoordinator("FutureModel", {"142": 2048})
    entity = IndevoltSensorEntity(coordinator, description)

    assert entity.native_value == 2048

    coordinator.data.pop("142")

    assert entity.native_value is None
    assert entity.available is True


def test_existing_firmware_sensor_formats_later_null_as_text() -> None:
    description = next(item for item in SENSORS_GEN2 if item.key == "1118")
    coordinator = FakeCoordinator("FutureModel", {"1118": 12345})
    entity = IndevoltSensorEntity(coordinator, description)

    assert entity.native_value == "1.23.45"

    coordinator.data["1118"] = None

    assert entity.native_value == "None"


def test_existing_cumulative_sensor_keeps_later_null_type_error() -> None:
    description = next(item for item in SENSORS_GEN1 if item.key == "1505")
    coordinator = FakeCoordinator("BK1600/BK1600Ultra", {"1505": 1000})
    entity = IndevoltSensorEntity(coordinator, description)

    coordinator.data["1505"] = None

    with pytest.raises(TypeError):
        _ = entity.native_value


def test_battery_sensor_reads_latest_value_but_availability_only_uses_serial() -> None:
    description = next(item for item in BATTERY_PACK_SENSORS[1] if item.key == "9016")
    coordinator = FakeCoordinator(
        "SolidFlex/PowerFlex2000",
        {"9032": "PACK-SN", "9016": 50},
    )
    entity = IndevoltBatterySensorEntity(coordinator, description, 1)

    assert entity.native_value == 50
    assert entity.available is True

    coordinator.data["9016"] = 75
    coordinator.last_update_success = False

    assert entity.native_value == 75
    assert entity.available is True

    coordinator.data.pop("9016")

    assert entity.native_value is None
    assert entity.available is True


@pytest.mark.parametrize(
    ("serial", "available", "name", "identifier"),
    [
        (None, False, "SFA/PFA Battery Pack 1 (None)", "battery_1_None"),
        ("", False, "SFA/PFA Battery Pack 1 (None)", "battery_1_"),
        (0, False, "SFA/PFA Battery Pack 1 (0)", "battery_1_0"),
        (False, False, "SFA/PFA Battery Pack 1 (False)", "battery_1_False"),
        ("PACK-SN", True, "SFA/PFA Battery Pack 1 (PACK-SN)", "battery_1_PACK-SN"),
    ],
)
def test_battery_identity_keeps_all_existing_serial_edge_cases(
    serial,
    available,
    name,
    identifier,
) -> None:
    description = next(item for item in BATTERY_PACK_SENSORS[1] if item.key == "9016")
    coordinator = FakeCoordinator("SolidFlex/PowerFlex2000", {"9032": serial})
    entity = IndevoltBatterySensorEntity(coordinator, description, 1)

    assert entity.available is available
    assert entity.device_info == {
        "identifiers": {(DOMAIN, identifier)},
        "name": name,
        "manufacturer": "INDEVOLT",
        "model": "Battery Pack",
        "serial_number": serial,
        "via_device": (DOMAIN, "MAIN-SN"),
    }
