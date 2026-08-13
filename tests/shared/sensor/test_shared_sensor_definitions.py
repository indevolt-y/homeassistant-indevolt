"""Golden contracts for every existing sensor description and conversion."""

from __future__ import annotations

import pytest

from custom_components.indevolt.sensor_descriptions.battery_pack import (
    BATTERY_PACK_SENSORS,
)
from custom_components.indevolt.sensor_descriptions.entity_description import (
    format_firmware_version,
)
from custom_components.indevolt.sensor_descriptions.gen1 import SENSORS_GEN1
from custom_components.indevolt.sensor_descriptions.gen2 import SENSORS_GEN2


def _value(value) -> str:
    """Normalize Home Assistant enums without importing expected constants."""
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def _signature(description) -> str:
    return "|".join(
        (
            description.key,
            description.name,
            description.translation_key,
            _value(description.native_unit_of_measurement),
            _value(description.device_class),
            _value(description.state_class),
            _value(description.entity_category),
        )
    )


GEN1_GOLDEN = """
1664|DC Input Power1|bk_series_dc_input_power_1|W|power|measurement|
1665|DC Input Power2|bk_series_dc_input_power_2|W|power|measurement|
2108|Total AC Output Power|total_ac_output_power|W|power|measurement|
1502|Daily Production|daily_production|kWh|energy|total_increasing|
1505|Cumulative Production|cumulative_production|kWh|energy|total_increasing|
2101|Total AC Input Power|total_ac_input_power|W|power|measurement|
2107|Total AC Input Energy|total_ac_input_energy|kWh|energy|total_increasing|
1501|Total DC Output Power|total_dc_output_power|W|power|measurement|
6000|Battery Power|battery_power|W|power|measurement|
6002|Battery SOC|battery_soc|%|battery|measurement|
6105|Emergency power supply|emergency_power_supply_soc|%|battery|measurement|
6004|Battery Daily Charging Energy|battery_daily_charging_energy|kWh|energy|total_increasing|
6005|Battery Daily Discharging Energy|battery_daily_discharging_energy|kWh|energy|total_increasing|
6006|Battery Total Charging Energy|battery_total_charging_energy|kWh|energy|total_increasing|
6007|Battery Total Discharging Energy|battery_total_discharging_energy|kWh|energy|total_increasing|
21028|Meter Power|meter_power|W|power|measurement|
7101|Working mode|working_mode||enum||diagnostic
6001|Battery Charge/Discharge State|battery_charge_discharge_state||enum||diagnostic
7120|Meter Connection Status|meter_connection_status||enum||diagnostic
""".strip()

GEN2_GOLDEN = """
1118|Firmware PG2000Series EMS|firmware_pg2000_series_ems||||diagnostic
1109|Firmware PG2000Series BMS-MB|firmware_pg2000_series_bms_mb||||diagnostic
1119|Firmware PG2000Series PCS|firmware_pg2000_series_pcs||||diagnostic
1120|Firmware PG2000Series DCDC|firmware_pg2000_series_dcdc||||diagnostic
142|Rated Capacity|rated_capacity|kWh|energy|total_increasing|
2101|Total AC Input Power|total_ac_input_power|W|power|measurement|
2108|Total AC Output Power|total_ac_output_power|W|power|measurement|
606|Master-Slave Identification|master_slave_identification||enum||diagnostic
667|Bypass Power|bypass_power|W|power|measurement|
2107|Total AC Input Energy|total_ac_input_energy|kWh|energy|total_increasing|
2104|Total AC Output Energy|total_ac_output_energy|kWh|energy|total_increasing|
2105|Off-grid Output Energy|off_grid_output_energy|kWh|energy|total_increasing|
11034|Bypass Input Energy|bypass_input_energy|Wh|energy|total_increasing|
1502|Daily Production|daily_production|kWh|energy|total_increasing|
6004|Battery Daily Charging Energy|battery_daily_charging_energy|kWh|energy|total_increasing|
6005|Battery Daily Discharging Energy|battery_daily_discharging_energy|kWh|energy|total_increasing|
6006|Battery Total Charging Energy|battery_total_charging_energy|kWh|energy|total_increasing|
6007|Battery Total Discharging Energy|battery_total_discharging_energy|kWh|energy|total_increasing|
7120|Meter Connection Status|meter_connection_status||enum||diagnostic
11016|Meter Power|meter_power|W|power|measurement|
2600|Grid Voltage|grid_voltage|V|voltage|measurement|
2612|Grid Frequency|grid_frequency|Hz|frequency|measurement|
6000|Battery Power|battery_power|W|power|measurement|
6002|Battery SOC Total|battery_soc_total|%|battery|measurement|
9008|Battery SN-MB|battery_serial_number_mb||||diagnostic
9000|Battery SOC-MB|battery_soc_mb|%|battery|measurement|
9004|Battery V-MB|battery_voltage_mb|V|voltage|measurement|
9013|Battery I-MB|battery_current_mb|A|current|measurement|
9012|Battery Temp-MB|battery_temperature_mb|°C|temperature|measurement|
9009|Battery Cell1 V-MB|battery_cell_1_voltage_mb|V|voltage|measurement|
9011|Battery Cell2 V-MB|battery_cell_2_voltage_mb|V|voltage|measurement|
1501|Total DC Output Power|total_dc_output_power|W|power|measurement|
1632|DC Input Current 1|dc_input_current_1|A|current|measurement|
1600|DC Input Voltage 1|dc_input_voltage_1|V|voltage|measurement|
1664|DC Input Power 1|dc_input_power_1|W|power|measurement|
1633|DC Input Current 2|dc_input_current_2|A|current|measurement|
1601|DC Input Voltage 2|dc_input_voltage_2|V|voltage|measurement|
1665|DC Input Power 2|dc_input_power_2|W|power|measurement|
1634|DC Input Current 3|dc_input_current_3|A|current|measurement|
1602|DC Input Voltage 3|dc_input_voltage_3|V|voltage|measurement|
1666|DC Input Power 3|dc_input_power_3|W|power|measurement|
1635|DC Input Current 4|dc_input_current_4|A|current|measurement|
1603|DC Input Voltage 4|dc_input_voltage_4|V|voltage|measurement|
1667|DC Input Power 4|dc_input_power_4|W|power|measurement|
""".strip()

BATTERY_GOLDEN = {
    1: """
1136|Firmware SFA/PFA DCDC1|battery_pack_1_firmware_dcdc||||diagnostic
1137|Firmware SFA/PFA BMS1|battery_pack_1_firmware_bms||||diagnostic
19173|Battery I-Pack1|battery_pack_1_current|A|current|measurement|
9016|Battery SOC-Pack1|battery_pack_1_soc|%|battery|measurement|
9020|Battery V-Pack1|battery_pack_1_voltage|V|voltage|measurement|
9021|Battery Cell1 V-Pack1|battery_pack_1_cell_1_voltage|V|voltage|measurement|
9023|Battery Cell2 V-Pack1|battery_pack_1_cell_2_voltage|V|voltage|measurement|
9030|Battery Temp-Pack1|battery_pack_1_temperature|°C|temperature|measurement|
""".strip(),
    2: """
1138|Firmware SFA/PFA DCDC2|battery_pack_2_firmware_dcdc||||diagnostic
1139|Firmware SFA/PFA BMS2|battery_pack_2_firmware_bms||||diagnostic
19174|Battery I-Pack2|battery_pack_2_current|A|current|measurement|
9035|Battery SOC-Pack2|battery_pack_2_soc|%|battery|measurement|
9039|Battery V-Pack2|battery_pack_2_voltage|V|voltage|measurement|
9040|Battery Cell1 V-Pack2|battery_pack_2_cell_1_voltage|V|voltage|measurement|
9042|Battery Cell2 V-Pack2|battery_pack_2_cell_2_voltage|V|voltage|measurement|
9049|Battery Temp-Pack2|battery_pack_2_temperature|°C|temperature|measurement|
""".strip(),
    3: """
1140|Firmware SFA/PFA DCDC3|battery_pack_3_firmware_dcdc||||diagnostic
1141|Firmware SFA/PFA BMS3|battery_pack_3_firmware_bms||||diagnostic
19175|Battery I-Pack3|battery_pack_3_current|A|current|measurement|
9054|Battery SOC-Pack3|battery_pack_3_soc|%|battery|measurement|
9058|Battery V-Pack3|battery_pack_3_voltage|V|voltage|measurement|
9059|Battery Cell1 V-Pack3|battery_pack_3_cell_1_voltage|V|voltage|measurement|
9061|Battery Cell2 V-Pack3|battery_pack_3_cell_2_voltage|V|voltage|measurement|
9068|Battery Temp-Pack3|battery_pack_3_temperature|°C|temperature|measurement|
""".strip(),
    4: """
1142|Firmware SFA/PFA DCDC4|battery_pack_4_firmware_dcdc||||diagnostic
1143|Firmware SFA/PFA BMS4|battery_pack_4_firmware_bms||||diagnostic
19176|Battery I-Pack4|battery_pack_4_current|A|current|measurement|
9149|Battery SOC-Pack4|battery_pack_4_soc|%|battery|measurement|
9153|Battery V-Pack4|battery_pack_4_voltage|V|voltage|measurement|
9154|Battery Cell1 V-Pack4|battery_pack_4_cell_1_voltage|V|voltage|measurement|
9156|Battery Cell2 V-Pack4|battery_pack_4_cell_2_voltage|V|voltage|measurement|
9163|Battery Temp-Pack4|battery_pack_4_temperature|°C|temperature|measurement|
""".strip(),
    5: """
1098|Firmware SFA/PFA DCDC5|battery_pack_5_firmware_dcdc||||diagnostic
1099|Firmware SFA/PFA BMS5|battery_pack_5_firmware_bms||||diagnostic
19177|Battery I-Pack5|battery_pack_5_current|A|current|measurement|
9202|Battery SOC-Pack5|battery_pack_5_soc|%|battery|measurement|
9206|Battery V-Pack5|battery_pack_5_voltage|V|voltage|measurement|
9216|Battery Temp-Pack5|battery_pack_5_temperature|°C|temperature|measurement|
9219|Battery Cell1 V-Pack5|battery_pack_5_cell_1_voltage|V|voltage|measurement|
9222|Battery Cell2 V-Pack5|battery_pack_5_cell_2_voltage|V|voltage|measurement|
""".strip(),
}


def test_gen1_sensor_descriptions_match_the_complete_golden_contract() -> None:
    assert "\n".join(map(_signature, SENSORS_GEN1)) == GEN1_GOLDEN


def test_gen2_sensor_descriptions_match_the_complete_golden_contract() -> None:
    assert "\n".join(map(_signature, SENSORS_GEN2)) == GEN2_GOLDEN


@pytest.mark.parametrize("pack_id", [1, 2, 3, 4, 5])
def test_each_battery_pack_matches_its_complete_golden_contract(pack_id) -> None:
    descriptions = sorted(BATTERY_PACK_SENSORS[pack_id], key=lambda item: item.key)
    assert "\n".join(map(_signature, descriptions)) == BATTERY_GOLDEN[pack_id]


def _description(descriptions, key):
    return next(item for item in descriptions if item.key == key)


def test_all_plain_sensor_value_functions_are_identity_functions() -> None:
    marker = object()
    gen1_special = {"1505", "7101", "6001", "7120"}
    gen2_special = {"1118", "1109", "1119", "1120", "606", "7120"}

    assert all(
        description.value_fn(marker) is marker
        for description in SENSORS_GEN1
        if description.key not in gen1_special
    )
    assert all(
        description.value_fn(marker) is marker
        for description in SENSORS_GEN2
        if description.key not in gen2_special
    )

    for descriptions in BATTERY_PACK_SENSORS.values():
        for description in descriptions:
            if description.entity_category is None:
                assert description.value_fn(marker) is marker


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        (12345, "1.23.45"),
        (123, "1.23"),
        ("01234", "0.12.34"),
        ("001", "0.01"),
        (12, "12"),
        (1234, "1234"),
        (None, "None"),
        ("", ""),
    ],
)
def test_firmware_formatter_keeps_every_existing_length_branch(
    version, expected
) -> None:
    assert format_firmware_version(version) == expected


@pytest.mark.parametrize("version", ["x12", "x1234"])
def test_firmware_formatter_keeps_invalid_leading_digit_failure(version) -> None:
    with pytest.raises(ValueError):
        format_firmware_version(version)


def test_every_firmware_sensor_uses_the_same_formatter() -> None:
    firmware_descriptions = [
        *(
            item
            for item in SENSORS_GEN2
            if item.key in {"1118", "1109", "1119", "1120"}
        ),
        *(
            item
            for descriptions in BATTERY_PACK_SENSORS.values()
            for item in descriptions
            if item.entity_category is not None
        ),
    ]

    assert len(firmware_descriptions) == 14
    assert all(item.value_fn(12345) == "1.23.45" for item in firmware_descriptions)


def test_gen1_special_sensor_conversions_are_fully_frozen() -> None:
    cumulative = _description(SENSORS_GEN1, "1505").value_fn
    work_mode = _description(SENSORS_GEN1, "7101").value_fn
    battery_state = _description(SENSORS_GEN1, "6001").value_fn
    meter_status = _description(SENSORS_GEN1, "7120").value_fn

    assert [cumulative(value) for value in (0, 1, 1000, -1000, 2.5)] == [
        0,
        0.001,
        1,
        -1,
        0.0025,
    ]
    assert {value: work_mode(value) for value in (0, 1, 4, 5, 2, None)} == {
        0: "Outdoor Portable",
        1: "Self-consumed Prioritized",
        4: "Real-Time Control",
        5: "Charge/Discharge Schedule",
        2: None,
        None: None,
    }
    assert {value: battery_state(value) for value in (1000, 1001, 1002, 0, None)} == {
        1000: "Static",
        1001: "Charging",
        1002: "Discharging",
        0: None,
        None: None,
    }
    assert {value: meter_status(value) for value in (1000, 1001, 0, None)} == {
        1000: "ON",
        1001: "OFF",
        0: None,
        None: None,
    }


def test_gen2_enum_conversions_keep_wire_type_and_unknown_behavior() -> None:
    master_slave = _description(SENSORS_GEN2, "606").value_fn
    meter_status = _description(SENSORS_GEN2, "7120").value_fn

    assert {
        value: master_slave(value) for value in ("1000", "1001", "1002", 1000, None)
    } == {
        "1000": "Master",
        "1001": "Slave",
        "1002": "None",
        1000: None,
        None: None,
    }
    assert {value: meter_status(value) for value in (1000, 1001, "1000", None)} == {
        1000: "ON",
        1001: "OFF",
        "1000": None,
        None: None,
    }
