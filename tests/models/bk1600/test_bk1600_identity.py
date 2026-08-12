"""BK1600 entity identity contract."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.indevolt.const import DOMAIN
from custom_components.indevolt.number import NUMBERS_GEN1, IndevoltNumberEntity
from custom_components.indevolt.select import SELECTS_GEN1, IndevoltSelectEntity
from custom_components.indevolt.sensor import IndevoltSensorEntity
from custom_components.indevolt.sensor_descriptions.gen1 import SENSORS_GEN1

MODEL = "BK1600/BK1600Ultra"


class FakeCoordinator:
    def __init__(self, data=None) -> None:
        self.config_entry = SimpleNamespace(
            unique_id="bk1600-entry",
            data={
                "sn": "BK1600-SN",
                "device_model": MODEL,
                "fw_version": "2.0.0",
            },
        )
        self.data = dict(data or {})


def test_bk1600_sensor_uses_its_config_entry_identity() -> None:
    coordinator = FakeCoordinator({"1664": 800})
    description = next(item for item in SENSORS_GEN1 if item.key == "1664")
    entity = IndevoltSensorEntity(coordinator, description)

    assert entity.unique_id == "bk1600-entry_1664"
    assert entity.device_info == {
        "identifiers": {(DOMAIN, "BK1600-SN")},
        "name": f"{MODEL} (BK1600-SN)",
        "manufacturer": "INDEVOLT",
        "sw_version": "2.0.0",
        "model": MODEL,
        "serial_number": "BK1600-SN",
    }


def test_bk1600_controls_share_its_config_entry_identity() -> None:
    coordinator = FakeCoordinator()
    entities = [
        IndevoltNumberEntity(coordinator, NUMBERS_GEN1[0]),
        IndevoltSelectEntity(coordinator, SELECTS_GEN1[0]),
    ]

    assert [entity.unique_id for entity in entities] == [
        "bk1600-entry_power_setting",
        "bk1600-entry_state_setting",
    ]
    assert all(
        entity.device_info["identifiers"] == {(DOMAIN, "BK1600-SN")}
        for entity in entities
    )
