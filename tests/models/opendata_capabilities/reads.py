"""Guessed Home Assistant entities for documented OpenData read points."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory

from .definitions import GetUserCapability

DCDC_STATE_CASES = (
    (0, "standby"),
    (2, "discharging"),
    (3, "protection"),
)
PV_OPERATING_STATE_CASES = (
    (2, "sleep"),
    (3, "starting"),
    (4, "running"),
    (5, "power_limited_operation"),
    (6, "shutting_down"),
    (7, "fault"),
    (8, "standby"),
    (9, "test_mode"),
)
PV_ALARM_CASES = (
    (3, "pv_input_disconnected"),
    (12, "pv_module_input_short_circuit"),
    (13, "pv_module_low_temperature"),
    (19, "pv_input_reverse_polarity"),
    (21, "pv_input_undervoltage"),
)
INVERTER_FAULT_CASES = (
    (2, "ac_connection_disconnected"),
    (3, "dc_connection_disconnected"),
    (4, "grid_connection_disconnected"),
    (5, "ground_fault"),
    (6, "ac_output_short_circuit"),
    (7, "inverter_overtemperature"),
    (8, "inverter_overfrequency"),
    (9, "inverter_underfrequency"),
    (10, "ac_input_overvoltage"),
    (11, "ac_input_undervoltage"),
    (12, "inverter_input_short_circuit"),
    (13, "inverter_low_temperature"),
    (19, "off_grid_inverter_phase_a_overvoltage"),
    (20, "off_grid_inverter_phase_a_undervoltage"),
    (21, "off_grid_inverter_phase_a_overcurrent_overload"),
)
SYSTEM_OPERATING_STATE_CASES = (
    (2, "sleep"),
    (3, "starting"),
    (4, "mppt_operating"),
    (5, "current_limiting"),
    (6, "shutting_down"),
    (7, "inverter_fault"),
    (8, "standby"),
    (9, "grid_charging"),
    (10, "grid_discharging"),
    (11, "off_grid_charging"),
    (12, "off_grid_discharging"),
    (13, "low_battery_charging"),
    (14, "deep_sleep"),
    (15, "scheduled_full_charge"),
    (16, "off_grid_deep_sleep"),
)


def _translation_key(name: str) -> str:
    """Return a stable test-side translation key for one new entity."""
    normalized = name.lower().replace("dc/dc", "dc dc").replace("/", " ")
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def _enum_options(
    sample: int,
    state: str,
    cases: tuple[tuple[Any, str], ...],
) -> tuple[str, ...]:
    """Return enum options in protocol-value order."""
    return tuple(option for _value, option in sorted(((sample, state), *cases)))


def _sensor_metadata(
    name: str,
    unit: str | None,
) -> tuple[SensorDeviceClass | None, SensorStateClass | None]:
    """Choose HA metadata from the documented physical meaning."""
    if unit == "W":
        return SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT
    if unit == "VA":
        return SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT
    if unit == "var":
        return SensorDeviceClass.REACTIVE_POWER, SensorStateClass.MEASUREMENT
    if unit == "V":
        return SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT
    if unit == "A":
        return SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT
    if unit == "Hz":
        return SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT
    if unit == "°C":
        return SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT
    if unit == "min":
        return SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT
    if unit in {"Wh", "kWh"}:
        if "Rated Capacity" in name:
            return SensorDeviceClass.ENERGY_STORAGE, SensorStateClass.MEASUREMENT
        if name.startswith("Daily "):
            return SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING
        return SensorDeviceClass.ENERGY, SensorStateClass.TOTAL
    if unit == "%":
        if "SOC" in name:
            return SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT
        if "Power Factor" in name:
            return SensorDeviceClass.POWER_FACTOR, SensorStateClass.MEASUREMENT
        return None, SensorStateClass.MEASUREMENT
    if "Cycle Count" in name:
        return None, SensorStateClass.TOTAL
    return None, None


def _diagnostic_category(name: str) -> EntityCategory | None:
    """Classify values which describe configuration or device health."""
    diagnostic_terms = (
        "Alarm",
        "Control Order",
        "Cycle Count",
        "Date and Time",
        "Fault",
        "Maximum",
        "Mode",
        "Operating Status",
        "Parallel Type",
        "Protocol Version",
        "Rated",
        "SOH",
        "Status",
        "Timeout",
        "Version",
    )
    return (
        EntityCategory.DIAGNOSTIC
        if any(term in name for term in diagnostic_terms)
        else None
    )


def _sensor(
    point: int,
    name: str,
    *,
    sample: Any = 1,
    state: str | None = None,
    unit: str | None = None,
    scope: str = "main",
    enabled: bool = True,
    cases: tuple[tuple[Any, str], ...] = (),
    translation_key: str | None = None,
    entity_category: EntityCategory | None = None,
    suggested_display_precision: int | None = None,
    options: tuple[str, ...] = (),
) -> GetUserCapability:
    device_class, state_class = _sensor_metadata(name, unit)
    if options:
        device_class = SensorDeviceClass.ENUM
        state_class = None
    return GetUserCapability(
        point=point,
        domain="sensor",
        key=str(point),
        name=name,
        translation_key=translation_key or _translation_key(name),
        sample_value=sample,
        expected_state=str(sample) if state is None else state,
        scope=scope,
        unit=unit,
        device_class=device_class,
        state_class=state_class,
        entity_category=entity_category or _diagnostic_category(name),
        suggested_display_precision=suggested_display_precision,
        options=options,
        enabled_by_default=enabled,
        additional_state_cases=cases,
    )


def _binary(
    point: int,
    name: str,
    *,
    scope: str = "main",
    device_class: BinarySensorDeviceClass | None = None,
    entity_category: EntityCategory | None = EntityCategory.DIAGNOSTIC,
) -> GetUserCapability:
    if scope.startswith("battery_"):
        pack_id = scope.removeprefix("battery_")
        name = name.removeprefix(f"Battery Pack {pack_id} ")
    return GetUserCapability(
        point=point,
        domain="binary_sensor",
        key=str(point),
        name=name,
        translation_key=_translation_key(name),
        sample_value=1,
        expected_state="on",
        scope=scope,
        device_class=device_class,
        entity_category=entity_category,
        additional_state_cases=((0, "off"),),
    )


def _pack_sensor(
    pack_id: int,
    point: int,
    name: str,
    *,
    unit: str | None = None,
    state: str | None = None,
    enabled: bool = True,
    cases: tuple[tuple[Any, str], ...] = (),
    options: tuple[str, ...] = (),
) -> GetUserCapability:
    name = name.removeprefix(f"Battery Pack {pack_id} ")
    return _sensor(
        point,
        name,
        unit=unit,
        state=state,
        scope=f"battery_{pack_id}",
        enabled=enabled,
        cases=cases,
        options=options,
    )


GET_USER_CAPABILITIES: tuple[GetUserCapability, ...] = (
    _sensor(2278, "Total AC Power", unit="W"),
    _sensor(11032, "Rated On-grid Power", unit="W"),
    _sensor(6010, "Maximum Battery Modules"),
    _sensor(114, "Maximum Charge Power", unit="W"),
    _sensor(115, "Maximum Discharge Power", unit="W"),
    _sensor(11019, "Remaining Charging Time", unit="min"),
    _sensor(11020, "Remaining Discharging Time", unit="min"),
    _sensor(9003, "Master Battery Cycle Count"),
    _pack_sensor(1, 9019, "Battery Pack 1 Cycle Count"),
    _pack_sensor(2, 9038, "Battery Pack 2 Cycle Count"),
    _pack_sensor(3, 9057, "Battery Pack 3 Cycle Count"),
    _pack_sensor(4, 9152, "Battery Pack 4 Cycle Count"),
    _pack_sensor(5, 9205, "Battery Pack 5 Cycle Count"),
    _sensor(9002, "Master Battery SOH", unit="%"),
    _pack_sensor(1, 9018, "Battery Pack 1 SOH", unit="%"),
    _pack_sensor(1, 9028, "Battery Pack 1 Minimum Cell Temperature", unit="°C"),
    _pack_sensor(2, 9037, "Battery Pack 2 SOH", unit="%"),
    _pack_sensor(2, 9047, "Battery Pack 2 Minimum Cell Temperature", unit="°C"),
    _pack_sensor(3, 9056, "Battery Pack 3 SOH", unit="%"),
    _pack_sensor(3, 9066, "Battery Pack 3 Minimum Cell Temperature", unit="°C"),
    _pack_sensor(4, 9151, "Battery Pack 4 SOH", unit="%"),
    _pack_sensor(4, 9161, "Battery Pack 4 Minimum Cell Temperature", unit="°C"),
    _sensor(9081, "Master Battery Heater Temperature", unit="°C"),
    _sensor(9082, "Master Battery Heater Power", unit="W"),
    _pack_sensor(1, 9097, "Battery Pack 1 Heater Temperature", unit="°C"),
    _pack_sensor(1, 9098, "Battery Pack 1 Heater Power", unit="W"),
    _pack_sensor(2, 9113, "Battery Pack 2 Heater Temperature", unit="°C"),
    _pack_sensor(2, 9114, "Battery Pack 2 Heater Power", unit="W"),
    _pack_sensor(3, 9129, "Battery Pack 3 Heater Temperature", unit="°C"),
    _pack_sensor(3, 9130, "Battery Pack 3 Heater Power", unit="W"),
    _pack_sensor(4, 9145, "Battery Pack 4 Heater Temperature", unit="°C"),
    _pack_sensor(4, 9146, "Battery Pack 4 Heater Power", unit="W"),
    _pack_sensor(5, 9204, "Battery Pack 5 SOH", unit="%"),
    _pack_sensor(5, 9214, "Battery Pack 5 Minimum Cell Temperature", unit="°C"),
    _pack_sensor(
        5,
        9267,
        "Battery Pack 5 Uplink Current",
        unit="A",
        enabled=False,
    ),
    _pack_sensor(5, 9280, "Battery Pack 5 Heater Temperature", unit="°C"),
    _pack_sensor(5, 9281, "Battery Pack 5 Heater Power", unit="W"),
    _sensor(9405, "System SOC", unit="%"),
    _sensor(
        9079,
        "Master Battery DC/DC Status",
        state="charging",
        cases=DCDC_STATE_CASES,
        options=_enum_options(1, "charging", DCDC_STATE_CASES),
    ),
    _binary(
        9080,
        "Master Battery Heater",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    _pack_sensor(
        1,
        9095,
        "Battery Pack 1 DC/DC Status",
        state="charging",
        cases=DCDC_STATE_CASES,
        options=_enum_options(1, "charging", DCDC_STATE_CASES),
    ),
    _binary(
        9096,
        "Battery Pack 1 Heater",
        scope="battery_1",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    _pack_sensor(
        2,
        9111,
        "Battery Pack 2 DC/DC Status",
        state="charging",
        cases=DCDC_STATE_CASES,
        options=_enum_options(1, "charging", DCDC_STATE_CASES),
    ),
    _binary(
        9112,
        "Battery Pack 2 Heater",
        scope="battery_2",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    _pack_sensor(
        3,
        9127,
        "Battery Pack 3 DC/DC Status",
        state="charging",
        cases=DCDC_STATE_CASES,
        options=_enum_options(1, "charging", DCDC_STATE_CASES),
    ),
    _binary(
        9128,
        "Battery Pack 3 Heater",
        scope="battery_3",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    _pack_sensor(
        4,
        9143,
        "Battery Pack 4 DC/DC Status",
        state="charging",
        cases=DCDC_STATE_CASES,
        options=_enum_options(1, "charging", DCDC_STATE_CASES),
    ),
    _binary(
        9144,
        "Battery Pack 4 Heater",
        scope="battery_4",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    _pack_sensor(
        5,
        9278,
        "Battery Pack 5 DC/DC Status",
        state="charging",
        cases=((0, "standby"), (2, "discharging")),
        options=("standby", "charging", "discharging"),
    ),
    _binary(
        9279,
        "Battery Pack 5 Heater",
        scope="battery_5",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    _binary(64100, "Critical Load Enabled", entity_category=None),
    _sensor(
        669,
        "Parallel Type",
        state="coordinated",
        cases=((0, "centralized"),),
        options=("centralized", "coordinated"),
    ),
    _sensor(4, "Rated Output Power", unit="W"),
    _sensor(614, "Maximum Active Power", unit="W"),
    _sensor(11028, "Rated Off-grid Voltage", unit="V"),
    _sensor(11029, "Rated Off-grid Frequency", unit="Hz"),
    _sensor(11030, "Rated Off-grid Power", unit="W"),
    _sensor(2086, "Inverter Input/Output Current", unit="A"),
    _sensor(2083, "Inverter Input/Output Voltage", unit="V"),
    _sensor(2095, "Inverter Input/Output Frequency", unit="Hz"),
    _sensor(2098, "Inverter Apparent Power", unit="VA"),
    _sensor(2097, "Inverter Reactive Power", unit="var"),
    _sensor(2099, "Inverter Power Factor", unit="%"),
    _sensor(2275, "Directional Inverter Power", unit="W"),
    _sensor(
        8100,
        "Inverter Fault",
        state="dc_side_overvoltage",
        cases=INVERTER_FAULT_CASES,
        options=_enum_options(1, "dc_side_overvoltage", INVERTER_FAULT_CASES),
    ),
    _sensor(11007, "Total Inverter Input Energy", unit="Wh"),
    _sensor(11036, "Daily Grid-connected Discharge Energy", unit="Wh"),
    _sensor(5000, "Home Load Power", unit="W"),
    _sensor(120, "Maximum MPPT Channels"),
    _sensor(11031, "Rated MPPT Power", unit="W"),
    _sensor(8500, "Total PV Charging Power", unit="W"),
    _sensor(
        7119,
        "PV 1 Operating Status",
        state="powered_off",
        cases=PV_OPERATING_STATE_CASES,
        options=_enum_options(1, "powered_off", PV_OPERATING_STATE_CASES),
    ),
    _sensor(
        7124,
        "PV 2 Operating Status",
        state="powered_off",
        cases=PV_OPERATING_STATE_CASES,
        options=_enum_options(1, "powered_off", PV_OPERATING_STATE_CASES),
    ),
    _sensor(
        7126,
        "PV 3 Operating Status",
        state="powered_off",
        cases=PV_OPERATING_STATE_CASES,
        options=_enum_options(1, "powered_off", PV_OPERATING_STATE_CASES),
    ),
    _sensor(
        7127,
        "PV 4 Operating Status",
        state="powered_off",
        cases=PV_OPERATING_STATE_CASES,
        options=_enum_options(1, "powered_off", PV_OPERATING_STATE_CASES),
    ),
    _sensor(
        8138,
        "PV 1 Alarm",
        state="pv_input_overvoltage",
        cases=PV_ALARM_CASES,
        options=_enum_options(1, "pv_input_overvoltage", PV_ALARM_CASES),
    ),
    _sensor(
        8102,
        "PV 2 Alarm",
        state="pv_input_overvoltage",
        cases=PV_ALARM_CASES,
        options=_enum_options(1, "pv_input_overvoltage", PV_ALARM_CASES),
    ),
    _sensor(
        8132,
        "PV 3 Alarm",
        state="pv_input_overvoltage",
        cases=PV_ALARM_CASES,
        options=_enum_options(1, "pv_input_overvoltage", PV_ALARM_CASES),
    ),
    _sensor(
        8133,
        "PV 4 Alarm",
        state="pv_input_overvoltage",
        cases=PV_ALARM_CASES,
        options=_enum_options(1, "pv_input_overvoltage", PV_ALARM_CASES),
    ),
    _sensor(1127, "Modbus Version", sample=15, state="V1.5"),
    _sensor(
        11006,
        "System Operating Status",
        state="powered_off",
        cases=SYSTEM_OPERATING_STATE_CASES,
        options=_enum_options(1, "powered_off", SYSTEM_OPERATING_STATE_CASES),
    ),
    _sensor(
        11008,
        "Device Date and Time",
        sample=(0x1A08, 0x0E0C, 0x2238),
        state="2026-08-14 12:34:56",
        cases=(((0x190C, 0x1F17, 0x3B3A), "2025-12-31 23:59:58"),),
    ),
    _sensor(632, "Standby Timeout"),
    GetUserCapability(
        point=35001,
        domain="time",
        key="deep_sleep_start_time",
        name="Deep Sleep Start Time",
        translation_key="deep_sleep_start_time",
        sample_value=0x121E,
        expected_state="18:30:00",
        entity_category=EntityCategory.CONFIG,
        additional_state_cases=((0x0000, "00:00:00"),),
    ),
    GetUserCapability(
        point=35002,
        domain="time",
        key="deep_sleep_end_time",
        name="Deep Sleep End Time",
        translation_key="deep_sleep_end_time",
        sample_value=0x061E,
        expected_state="06:30:00",
        entity_category=EntityCategory.CONFIG,
        additional_state_cases=((0x173B, "23:59:00"),),
    ),
    _sensor(
        6107,
        "Real-time Control Order",
        state="charge",
        cases=((0, "standby"), (2, "discharge")),
        options=("standby", "charge", "discharge"),
    ),
    _sensor(6109, "Real-time Control Power", unit="W"),
    _sensor(6108, "Real-time Control End SOC", unit="%"),
    _sensor(9284, "Total Bypass Port Discharge Energy", unit="Wh"),
    _sensor(9285, "Daily Bypass Discharge Energy", unit="Wh"),
    _sensor(11035, "Daily Microinverter Energy Generation", unit="Wh"),
    _sensor(
        11039,
        "Bypass Mode",
        sample=0,
        state="eps_mode",
        cases=((1, "microinverter_mode"),),
        options=("eps_mode", "microinverter_mode"),
    ),
    _sensor(11037, "Daily Off-grid Discharge Energy", unit="Wh"),
    _sensor(
        1505,
        "Cumulative Production",
        sample=2500,
        state="2.5",
        unit="kWh",
        suggested_display_precision=3,
        cases=((0, "0.0"), (1000, "1.0")),
    ),
    *(
        GetUserCapability(
            point=26000 + slot,
            domain="number",
            key=f"simulated_load_slot_{slot + 1:02d}",
            name=f"Simulated Load Time Slot {slot + 1}",
            translation_key="simulated_load_time_slot",
            translation_placeholders={"slot": str(slot + 1)},
            sample_value=100 + slot,
            expected_state=str(100 + slot),
            unit="W",
            device_class=NumberDeviceClass.POWER,
            entity_category=EntityCategory.CONFIG,
            icon="mdi:transmission-tower-import",
            enabled_by_default=False,
        )
        for slot in range(48)
    ),
)


BK_GET_USER_CAPABILITIES: tuple[GetUserCapability, ...] = (
    _sensor(1118, "BK1600 Series EMS Version", sample="EMS-1.0.0"),
    _sensor(1107, "BK1600 Series BMS Version", sample="BMS-1.0.0"),
    _sensor(1119, "BK1600 Series PCS Version", sample="PCS-1.0.0"),
    _sensor(311, "BK1600 Series MPPT Version", sample="MPPT-1.0.0"),
    _sensor(142, "Rated Capacity", unit="kWh"),
    GetUserCapability(
        point=2618,
        domain="binary_sensor",
        key="2618",
        name="Grid Charging",
        translation_key="grid_charging",
        sample_value=1001,
        expected_state="on",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        additional_state_cases=((1000, "off"),),
    ),
    _sensor(2617, "Feed-in Power Limit", unit="W"),
    _sensor(4, "Maximum AC Output Power", unit="W"),
    _sensor(2619, "Maximum AC Input Power", unit="W"),
    GetUserCapability(
        point=680,
        domain="binary_sensor",
        key="680",
        name="Bypass",
        translation_key="bypass",
        sample_value=1,
        expected_state="on",
        additional_state_cases=((0, "off"),),
    ),
    _sensor(
        7170,
        "Bypass Mode",
        sample=0,
        state="eps_mode",
        cases=((1, "microinverter_mode"),),
        options=("eps_mode", "microinverter_mode"),
    ),
    _sensor(7620, "Battery Temperature", unit="°C"),
    *(
        _sensor(10112 + cell - 1, f"Cell {cell} Voltage", unit="V")
        for cell in range(1, 12)
    ),
    _sensor(1632, "DC Input Current 1", unit="A"),
    _sensor(1600, "DC Input Voltage 1", unit="V"),
    _sensor(1633, "DC Input Current 2", unit="A"),
    _sensor(1601, "DC Input Voltage 2", unit="V"),
)
