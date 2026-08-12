"""PowerFlex2000 main-device and battery-pack identity contracts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.indevolt.const import DOMAIN
from custom_components.indevolt.number import NUMBERS_GEN2, IndevoltNumberEntity
from custom_components.indevolt.select import SELECTS_GEN2, IndevoltSelectEntity
from custom_components.indevolt.sensor import (
    IndevoltBatterySensorEntity,
    IndevoltSensorEntity,
)
from custom_components.indevolt.sensor_descriptions.battery_pack import (
    BATTERY_PACK_SENSORS,
)
from custom_components.indevolt.sensor_descriptions.gen2 import SENSORS_GEN2
from custom_components.indevolt.switch import SWITCHES, IndevoltSwitchEntity

MODEL = "PowerFlex2000"
PACK_CASES = [
    (1, "9032", "9016"),
    (2, "9051", "9035"),
    (3, "9070", "9054"),
    (4, "9165", "9149"),
    (5, "9218", "9202"),
]


class FakeCoordinator:
    def __init__(self, data=None) -> None:
        self.config_entry = SimpleNamespace(
            unique_id="powerflex2000-entry",
            data={
                "sn": "POWERFLEX2000-SN",
                "device_model": MODEL,
                "fw_version": "2.0.0",
            },
        )
        self.data = dict(data or {})
        self.last_update_success = True


def description_for_pack(pack_id: int, key: str):
    return next(
        description
        for description in BATTERY_PACK_SENSORS[pack_id]
        if description.key == key
    )


def test_powerflex2000_sensor_uses_its_config_entry_identity() -> None:
    coordinator = FakeCoordinator({"142": 2_048})
    description = next(item for item in SENSORS_GEN2 if item.key == "142")
    entity = IndevoltSensorEntity(coordinator, description)

    assert entity.unique_id == "powerflex2000-entry_142"
    assert entity.device_info == {
        "identifiers": {(DOMAIN, "POWERFLEX2000-SN")},
        "name": f"{MODEL} (POWERFLEX2000-SN)",
        "manufacturer": "INDEVOLT",
        "sw_version": "2.0.0",
        "model": MODEL,
        "serial_number": "POWERFLEX2000-SN",
    }


def test_powerflex2000_controls_share_its_config_entry_identity() -> None:
    coordinator = FakeCoordinator()
    entities = [
        IndevoltNumberEntity(coordinator, NUMBERS_GEN2[0]),
        IndevoltSelectEntity(coordinator, SELECTS_GEN2[0]),
        IndevoltSwitchEntity(coordinator, SWITCHES[0]),
    ]

    assert [entity.unique_id for entity in entities] == [
        "powerflex2000-entry_backup_soc",
        "powerflex2000-entry_work_mode",
        "powerflex2000-entry_light",
    ]
    assert all(
        entity.device_info["identifiers"] == {(DOMAIN, "POWERFLEX2000-SN")}
        for entity in entities
    )


@pytest.mark.parametrize(("pack_id", "serial_key", "sensor_key"), PACK_CASES)
def test_powerflex2000_battery_pack_has_stable_identity_and_parent(
    pack_id,
    serial_key,
    sensor_key,
) -> None:
    pack_serial = f"POWER-PACK-{pack_id}-SN"
    coordinator = FakeCoordinator({serial_key: pack_serial})
    entity = IndevoltBatterySensorEntity(
        coordinator,
        description_for_pack(pack_id, sensor_key),
        pack_id,
    )

    assert entity.unique_id == (f"powerflex2000-entry_battery_{pack_id}_{sensor_key}")
    assert entity.available is True
    assert entity.device_info == {
        "identifiers": {(DOMAIN, f"battery_{pack_id}_{pack_serial}")},
        "name": f"SFA/PFA Battery Pack {pack_id} ({pack_serial})",
        "manufacturer": "INDEVOLT",
        "model": "Battery Pack",
        "serial_number": pack_serial,
        "via_device": (DOMAIN, "POWERFLEX2000-SN"),
    }


def test_powerflex2000_battery_pack_without_serial_is_unavailable() -> None:
    coordinator = FakeCoordinator()
    entity = IndevoltBatterySensorEntity(
        coordinator,
        description_for_pack(1, "9016"),
        1,
    )

    assert entity.available is False
    assert entity.device_info["serial_number"] is None
