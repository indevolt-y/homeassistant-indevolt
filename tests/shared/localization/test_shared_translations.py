"""Shared Home Assistant localization contract."""

from __future__ import annotations

import json
from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
from string import Formatter
from typing import Any

import pytest
import yaml
from homeassistant import loader
from homeassistant.core import HomeAssistant
from homeassistant.helpers.translation import async_get_translations

from custom_components.indevolt.binary_sensor import (
    IndevoltCapabilityBinarySensorEntity,
)
from custom_components.indevolt.number import (
    NUMBERS_GEN1,
    NUMBERS_GEN2,
    IndevoltCapabilityNumberEntity,
    IndevoltNumberEntity,
)
from custom_components.indevolt.select import (
    SELECTS_GEN1,
    SELECTS_GEN2,
    IndevoltSelectEntity,
)
from custom_components.indevolt.sensor import (
    IndevoltBatterySensorEntity,
    IndevoltCapabilitySensorEntity,
    IndevoltSensorEntity,
)
from custom_components.indevolt.sensor_descriptions.battery_pack import (
    BATTERY_PACK_SENSORS,
)
from custom_components.indevolt.sensor_descriptions.gen1 import SENSORS_GEN1
from custom_components.indevolt.sensor_descriptions.gen2 import SENSORS_GEN2
from custom_components.indevolt.switch import SWITCHES, IndevoltSwitchEntity
from custom_components.indevolt.time import IndevoltCapabilityTimeEntity
from tests.models.opendata_capabilities import (
    BK_GET_USER_CAPABILITIES,
    GET_USER_CAPABILITIES,
    SET_USER_CAPABILITIES,
)

REPOSITORY_ROOT = Path(__file__).parents[3]
INTEGRATION_ROOT = REPOSITORY_ROOT / "custom_components" / "indevolt"
TRANSLATIONS_ROOT = INTEGRATION_ROOT / "translations"


def _load_json(language: str) -> dict[str, Any]:
    return json.loads((TRANSLATIONS_ROOT / f"{language}.json").read_text())


def _leaf_strings(value: Any, path: tuple[str, ...] = ()) -> dict[tuple[str, ...], str]:
    if isinstance(value, dict):
        leaves = {}
        for key, child in value.items():
            leaves.update(_leaf_strings(child, (*path, key)))
        return leaves
    assert isinstance(value, str)
    return {path: value}


def _placeholders(value: str) -> set[str]:
    return {
        field_name
        for _, field_name, _, _ in Formatter().parse(value)
        if field_name is not None
    }


def _translation_keys(descriptions: Iterable[Any]) -> set[str]:
    keys = {description.translation_key for description in descriptions}
    assert None not in keys
    return keys


def _description_by_key(descriptions: Iterable[Any], key: str) -> Any:
    return next(description for description in descriptions if description.key == key)


def test_translation_files_have_identical_contracts() -> None:
    assert {path.name for path in TRANSLATIONS_ROOT.iterdir()} == {
        "en.json",
        "zh-Hans.json",
    }
    assert not (INTEGRATION_ROOT / "strings.json").exists()

    english = _leaf_strings(_load_json("en"))
    chinese = _leaf_strings(_load_json("zh-Hans"))

    assert english.keys() == chinese.keys()
    assert {path: _placeholders(value) for path, value in english.items()} == {
        path: _placeholders(value) for path, value in chinese.items()
    }


def test_every_translation_text_matches_the_complete_golden_contract() -> None:
    """Lock every user-facing string, not only representative examples."""
    expected_hashes = {
        "en": "add13fc6d7907439655c4ff63b2230235c98784602a60fa8f925ecaf014dcb0a",
        "zh-Hans": "8eff6c38c0d66c21d73f7f9e9fc14f0fe7a7eaab19d2b77a2bf08e020b1c3210",
    }

    for language, expected_hash in expected_hashes.items():
        canonical_json = json.dumps(
            _load_json(language),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        assert sha256(canonical_json).hexdigest() == expected_hash


def test_every_entity_description_has_a_name_translation() -> None:
    english = _load_json("en")["entity"]
    chinese = _load_json("zh-Hans")["entity"]
    battery_sensors = tuple(
        description
        for sensors in BATTERY_PACK_SENSORS.values()
        for description in sensors
    )
    descriptions_by_platform = {
        "sensor": (*SENSORS_GEN1, *SENSORS_GEN2, *battery_sensors),
        "number": (*NUMBERS_GEN1, *NUMBERS_GEN2),
        "select": (*SELECTS_GEN1, *SELECTS_GEN2),
        "switch": tuple(SWITCHES),
        "binary_sensor": (),
        "time": (),
    }
    get_capabilities = (*GET_USER_CAPABILITIES, *BK_GET_USER_CAPABILITIES)

    for platform, existing_descriptions in descriptions_by_platform.items():
        descriptions = (
            *existing_descriptions,
            *(item for item in get_capabilities if item.domain == platform),
            *(
                item
                for item in SET_USER_CAPABILITIES
                if item.entity_domain == platform and item.translation_key is not None
            ),
        )
        expected_keys = _translation_keys(descriptions)
        assert set(english[platform]) == expected_keys
        assert set(chinese[platform]) == expected_keys
        assert all("name" in value for value in english[platform].values())
        assert all("name" in value for value in chinese[platform].values())
        for description in descriptions:
            placeholders = dict(
                getattr(description, "translation_placeholders", None) or {}
            )
            translation = english[platform][description.translation_key]
            assert translation["name"].format(**placeholders) == description.name
            options = tuple(getattr(description, "options", ()) or ())
            if options:
                assert set(options) <= set(translation["state"])
                assert set(options) <= set(
                    chinese[platform][description.translation_key]["state"]
                )

    for entity_class in (
        IndevoltSensorEntity,
        IndevoltBatterySensorEntity,
        IndevoltCapabilitySensorEntity,
        IndevoltCapabilityBinarySensorEntity,
        IndevoltCapabilityNumberEntity,
        IndevoltCapabilityTimeEntity,
        IndevoltNumberEntity,
        IndevoltSelectEntity,
        IndevoltSwitchEntity,
    ):
        assert object.__new__(entity_class).has_entity_name is True


def test_public_state_and_option_values_are_unchanged() -> None:
    gen1_work_mode = _description_by_key(SENSORS_GEN1, "7101").value_fn
    gen1_battery_state = _description_by_key(SENSORS_GEN1, "6001").value_fn
    gen1_meter_status = _description_by_key(SENSORS_GEN1, "7120").value_fn
    gen2_master_slave = _description_by_key(SENSORS_GEN2, "606").value_fn
    gen2_meter_status = _description_by_key(SENSORS_GEN2, "7120").value_fn

    assert {value: gen1_work_mode(value) for value in (0, 1, 4, 5)} == {
        0: "Outdoor Portable",
        1: "Self-consumed Prioritized",
        4: "Real-Time Control",
        5: "Charge/Discharge Schedule",
    }
    assert {value: gen1_battery_state(value) for value in (1000, 1001, 1002)} == {
        1000: "Static",
        1001: "Charging",
        1002: "Discharging",
    }
    assert {value: gen1_meter_status(value) for value in (1000, 1001)} == {
        1000: "ON",
        1001: "OFF",
    }
    assert {value: gen2_master_slave(value) for value in ("1000", "1001", "1002")} == {
        "1000": "Master",
        "1001": "Slave",
        "1002": "None",
    }
    assert {value: gen2_meter_status(value) for value in (1000, 1001)} == {
        1000: "ON",
        1001: "OFF",
    }

    assert [description.options_map for description in SELECTS_GEN1] == [
        {0: "Standby", 1: "Charging", 2: "Discharging"}
    ]
    assert list(SELECTS_GEN2[0].options_map.items())[:3] == [
        (1, "Self-Consumed Prioritized"),
        (4, "Real-Time Control"),
        (5, "Charge/Discharge Schedule"),
    ]
    assert SELECTS_GEN2[0].options_map[6] == "Custom Time Control Mode"
    assert [description.options_map for description in SELECTS_GEN2[1:]] == [
        {0: "Standby", 1: "Charging", 2: "Discharging"},
        {1: "Smart Plug", 2: "Meter", 3: "Key Load", 4: "Custom"},
        {0: "off", 1: "on", 2: "low_power"},
    ]


def test_action_selector_values_are_unchanged() -> None:
    services = yaml.safe_load((INTEGRATION_ROOT / "services.yaml").read_text())

    assert services["set_solidflex_powerflex_work_mode"]["fields"]["mode"]["selector"][
        "select"
    ]["options"] == [
        "Self-Consumed Prioritized",
        "Real-Time Control",
        "Charge/Discharge Schedule",
    ]
    assert services["set_solidflex_powerflex_work_mode"]["fields"]["state"]["selector"][
        "select"
    ]["options"] == ["Standby", "Charging", "Discharging"]
    assert services["set_bk1600_work_mode"]["fields"]["mode"]["selector"]["select"][
        "options"
    ] == ["Real-Time Control"]
    assert services["set_bk1600_work_mode"]["fields"]["state"]["selector"]["select"][
        "options"
    ] == ["Standby", "Charging", "Discharging"]

    for action in services.values():
        assert "name" not in action
        assert "description" not in action
        for field in action["fields"].values():
            assert "name" not in field
            assert "description" not in field


@pytest.mark.asyncio
async def test_home_assistant_loads_languages_and_english_fallback() -> None:
    hass = HomeAssistant(str(REPOSITORY_ROOT))
    loader.async_setup(hass)

    try:
        translations = {
            language: {
                category: await async_get_translations(
                    hass,
                    language,
                    category,
                    integrations={"indevolt"},
                )
                for category in ("config", "entity", "services")
            }
            for language in ("en", "zh-Hans", "de")
        }
    finally:
        await hass.async_stop(force=True)

    assert (
        translations["en"]["config"]["component.indevolt.config.step.user.data.host"]
        == "IP address"
    )
    assert (
        translations["zh-Hans"]["config"][
            "component.indevolt.config.step.user.data.host"
        ]
        == "IP 地址"
    )
    assert (
        translations["en"]["entity"][
            "component.indevolt.entity.sensor.dc_input_power_1.name"
        ]
        == "DC Input Power 1"
    )
    assert (
        translations["zh-Hans"]["entity"][
            "component.indevolt.entity.sensor.dc_input_power_1.name"
        ]
        == "直流输入 1 功率"
    )
    assert (
        translations["en"]["services"][
            "component.indevolt.services.set_bk1600_work_mode.name"
        ]
        == "Set BK1600/BK1600 Ultra Work Mode"
    )
    assert (
        translations["zh-Hans"]["services"][
            "component.indevolt.services.set_bk1600_work_mode.name"
        ]
        == "设置 BK1600/BK1600 Ultra 工作模式"
    )
    assert translations["de"] == translations["en"]
