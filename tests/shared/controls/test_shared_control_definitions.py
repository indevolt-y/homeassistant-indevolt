"""Golden metadata and read contracts for every control entity."""

from __future__ import annotations

from custom_components.indevolt.number import NUMBERS_GEN1, NUMBERS_GEN2
from custom_components.indevolt.select import SELECTS_GEN1, SELECTS_GEN2
from custom_components.indevolt.switch import SWITCHES


def _value(value) -> str:
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def _number_signature(description) -> str:
    return "|".join(
        map(
            str,
            (
                description.key,
                description.name,
                description.translation_key,
                _value(description.device_class),
                _value(description.entity_category),
                _value(description.mode),
                description.native_min_value,
                ""
                if description.native_max_value is None
                else description.native_max_value,
                description.native_step,
                _value(description.native_unit_of_measurement),
            ),
        )
    )


def _select_signature(description) -> tuple:
    return (
        description.key,
        description.name,
        description.translation_key,
        description.icon,
        description.read_point,
        _value(description.entity_category),
        description.options_map,
    )


def _switch_signature(description) -> tuple:
    return (
        description.key,
        description.name,
        description.translation_key,
        description.icon,
        description.read_point,
        _value(description.device_class),
    )


def test_number_descriptions_match_the_complete_golden_contract() -> None:
    assert list(map(_number_signature, NUMBERS_GEN1)) == [
        "power_setting|Power (Real-time control)|real_time_control_power|power|config|slider|0||1|W",
        "soc_setting|Target SOC (Real-time control)|real_time_control_target_soc|battery|config||0|100|1|%",
    ]
    assert list(map(_number_signature, NUMBERS_GEN2)) == [
        "backup_soc|Backup SOC|backup_soc|battery|config||5|100|1|%",
        "inverter_input_limit|Inverter Input Limit|inverter_input_limit|power|config||50|2400|1|W",
        "max_output_power|Max AC Output Power|max_ac_output_power|power|config||50|2400|1|W",
        "feed_in_power_limit|Feed-in Power Limit|feed_in_power_limit|power|config||50|2400|1|W",
        "power_setting|Power (Real-time control)|real_time_control_power|power|config||50|10800|1|W",
        "soc_setting|Target SOC (Real-time control)|real_time_control_target_soc|battery|config||5|100|1|%",
    ]


def test_number_read_functions_keep_the_complete_existing_mapping() -> None:
    data = {
        "6105": 71,
        "11009": 1200,
        "11011": 1800,
        "11010": 900,
    }

    assert {
        description.key: description.value_fn(data) for description in NUMBERS_GEN1
    } == {
        "power_setting": None,
        "soc_setting": None,
    }
    assert {
        description.key: description.value_fn(data) for description in NUMBERS_GEN2
    } == {
        "backup_soc": 71,
        "inverter_input_limit": 1200,
        "max_output_power": 1800,
        "feed_in_power_limit": 900,
        "power_setting": None,
        "soc_setting": None,
    }
    assert {
        description.key: description.value_fn({}) for description in NUMBERS_GEN2
    } == {
        "backup_soc": None,
        "inverter_input_limit": None,
        "max_output_power": None,
        "feed_in_power_limit": None,
        "power_setting": None,
        "soc_setting": None,
    }


def test_select_descriptions_match_the_complete_golden_contract() -> None:
    assert list(map(_select_signature, SELECTS_GEN1)) == [
        (
            "state_setting",
            "State (Real-time control)",
            "real_time_control_state",
            "mdi:cog",
            "6001",
            "config",
            {0: "Standby", 1: "Charging", 2: "Discharging"},
        )
    ]
    assert list(map(_select_signature, SELECTS_GEN2)) == [
        (
            "work_mode",
            "Work Mode",
            "work_mode",
            "mdi:cog",
            "7101",
            "config",
            {
                1: "Self-Consumed Prioritized",
                4: "Real-Time Control",
                5: "Charge/Discharge Schedule",
                6: "Custom Time Control Mode",
            },
        ),
        (
            "state_setting",
            "State (Real-time control)",
            "real_time_control_state",
            "mdi:cog",
            "6001",
            "config",
            {0: "Standby", 1: "Charging", 2: "Discharging"},
        ),
        (
            "load_setting",
            "Load Setting",
            "load_setting",
            "mdi:cog",
            "",
            "config",
            {1: "Smart Plug", 2: "Meter", 3: "Key Load", 4: "Custom"},
        ),
        (
            "led_light_strip_mode",
            "LED Light-strip Mode",
            "led_light_strip_mode",
            "mdi:led-strip-variant",
            "7171",
            "config",
            {0: "off", 1: "on", 2: "low_power"},
        ),
    ]


def test_switch_descriptions_match_the_complete_golden_contract() -> None:
    assert list(map(_switch_signature, SWITCHES)) == [
        ("light", "Light", "light", "mdi:led-on", "7171", "switch"),
        ("grid", "Grid Charging", "grid_charging", None, "2618", "outlet"),
        ("bypass", "Bypass", "bypass", None, "680", "outlet"),
    ]


def test_switch_read_create_and_available_functions_cover_all_wire_values() -> None:
    expected_on_value = {"light": 1, "grid": 1001, "bypass": 1}

    for description in SWITCHES:
        point = description.read_point
        assert description.create_fn({}) is False
        assert description.create_fn({point: None}) is True
        assert description.available_fn({}) is False
        assert description.available_fn({point: None}) is False
        assert description.is_on_fn({}) is False
        assert description.is_on_fn({point: None}) is False

        for value in (0, False, 1, True, 1000, 1001, "1"):
            data = {point: value}
            assert description.create_fn(data) is True
            assert description.available_fn(data) is True
            assert description.is_on_fn(data) is (
                value == expected_on_value[description.key]
            )
