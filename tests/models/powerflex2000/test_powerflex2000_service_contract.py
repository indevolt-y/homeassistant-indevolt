"""PowerFlex2000 services YAML, constant, and number-description contract."""

from __future__ import annotations

from pathlib import Path

import yaml

from custom_components.indevolt.const import MAX_REAL_TIME_CONTROL_POWER
from custom_components.indevolt.number import NUMBERS_GEN2


def test_powerflex2000_service_schema_matches_its_number_contract() -> None:
    services = yaml.safe_load(
        (
            Path(__file__).parents[3]
            / "custom_components"
            / "indevolt"
            / "services.yaml"
        ).read_text()
    )
    selector = services["set_solidflex_powerflex_work_mode"]["fields"]["power"][
        "selector"
    ]["number"]
    power = next(item for item in NUMBERS_GEN2 if item.key == "power_setting")

    assert MAX_REAL_TIME_CONTROL_POWER == 10_800
    assert selector == {
        "min": 50,
        "max": MAX_REAL_TIME_CONTROL_POWER,
        "step": 10,
        "unit_of_measurement": "W",
    }
    assert power.native_max_value == MAX_REAL_TIME_CONTROL_POWER
    assert power.native_min_value == 50
    assert power.native_step == 1
