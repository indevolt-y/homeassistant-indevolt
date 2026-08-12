"""BK1600 services YAML and number-description contract."""

from __future__ import annotations

from pathlib import Path

import yaml

from custom_components.indevolt.number import NUMBERS_GEN1


def test_bk1600_service_schema_matches_its_number_contract() -> None:
    services = yaml.safe_load(
        (
            Path(__file__).parents[3]
            / "custom_components"
            / "indevolt"
            / "services.yaml"
        ).read_text()
    )
    selector = services["set_bk1600_work_mode"]["fields"]["power"]["selector"]["number"]
    power = next(item for item in NUMBERS_GEN1 if item.key == "power_setting")

    assert power.native_max_value is None
    assert selector == {
        "min": 0,
        "max": 1_200,
        "step": 10,
        "unit_of_measurement": "W",
    }
