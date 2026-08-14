"""Guessed Home Assistant entities for documented OpenData read points."""

from __future__ import annotations

from typing import Any

from .definitions import GetUserCapability


def _sensor(
    point: int,
    name: str,
    *,
    sample: Any = 1,
    state: str | None = None,
    unit: str | None = None,
    scope: str = "main",
    enabled: bool = True,
) -> GetUserCapability:
    return GetUserCapability(
        point=point,
        domain="sensor",
        key=str(point),
        name=name,
        sample_value=sample,
        expected_state=str(sample) if state is None else state,
        scope=scope,
        unit=unit,
        enabled_by_default=enabled,
    )


def _binary(
    point: int,
    name: str,
    *,
    scope: str = "main",
) -> GetUserCapability:
    if scope.startswith("battery_"):
        pack_id = scope.removeprefix("battery_")
        name = name.removeprefix(f"Battery Pack {pack_id} ")
    return GetUserCapability(
        point=point,
        domain="binary_sensor",
        key=str(point),
        name=name,
        sample_value=1,
        expected_state="on",
        scope=scope,
    )


def _pack_sensor(
    pack_id: int,
    point: int,
    name: str,
    *,
    unit: str | None = None,
    state: str | None = None,
    enabled: bool = True,
) -> GetUserCapability:
    name = name.removeprefix(f"Battery Pack {pack_id} ")
    return _sensor(
        point,
        name,
        unit=unit,
        state=state,
        scope=f"battery_{pack_id}",
        enabled=enabled,
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
    _sensor(9079, "Master Battery DC/DC Status", state="Charging"),
    _binary(9080, "Master Battery Heater"),
    _pack_sensor(1, 9095, "Battery Pack 1 DC/DC Status", state="Charging"),
    _binary(9096, "Battery Pack 1 Heater", scope="battery_1"),
    _pack_sensor(2, 9111, "Battery Pack 2 DC/DC Status", state="Charging"),
    _binary(9112, "Battery Pack 2 Heater", scope="battery_2"),
    _pack_sensor(3, 9127, "Battery Pack 3 DC/DC Status", state="Charging"),
    _binary(9128, "Battery Pack 3 Heater", scope="battery_3"),
    _pack_sensor(4, 9143, "Battery Pack 4 DC/DC Status", state="Charging"),
    _binary(9144, "Battery Pack 4 Heater", scope="battery_4"),
    _pack_sensor(5, 9278, "Battery Pack 5 DC/DC Status", state="Charging"),
    _binary(9279, "Battery Pack 5 Heater", scope="battery_5"),
    _binary(64100, "Critical Load Enabled"),
    _sensor(669, "Parallel Type", state="Coordinated"),
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
    _sensor(8100, "Inverter Fault", state="DC Side Overvoltage"),
    _sensor(11007, "Total Inverter Input Energy", unit="Wh"),
    _sensor(11036, "Daily Grid-connected Discharge Energy", unit="Wh"),
    _sensor(5000, "Home Load Power", unit="W"),
    _sensor(120, "Maximum MPPT Channels"),
    _sensor(11031, "Rated MPPT Power", unit="W"),
    _sensor(8500, "Total PV Charging Power", unit="W"),
    _sensor(7119, "PV 1 Operating Status", state="Powered Off"),
    _sensor(7124, "PV 2 Operating Status", state="Powered Off"),
    _sensor(7126, "PV 3 Operating Status", state="Powered Off"),
    _sensor(7127, "PV 4 Operating Status", state="Powered Off"),
    _sensor(8138, "PV 1 Alarm", state="PV Input Overvoltage"),
    _sensor(8102, "PV 2 Alarm", state="PV Input Overvoltage"),
    _sensor(8132, "PV 3 Alarm", state="PV Input Overvoltage"),
    _sensor(8133, "PV 4 Alarm", state="PV Input Overvoltage"),
    _sensor(1127, "OpenData Protocol Version", sample=15, state="V1.5"),
    _sensor(11006, "System Operating Status", state="Powered Off"),
    _sensor(
        11008,
        "Device Date and Time",
        sample=(0x1A08, 0x0E0C, 0x2238),
        state="2026-08-14 12:34:56",
    ),
    _sensor(632, "Standby Timeout"),
    GetUserCapability(
        35001,
        "time",
        "deep_sleep_start_time",
        "Deep Sleep Start Time",
        0x121E,
        "18:30:00",
    ),
    GetUserCapability(
        35002,
        "time",
        "deep_sleep_end_time",
        "Deep Sleep End Time",
        0x061E,
        "06:30:00",
    ),
    _sensor(6107, "Real-time Control Order", state="Charge"),
    _sensor(6109, "Real-time Control Power", unit="W"),
    _sensor(6108, "Real-time Control End SOC", unit="%"),
    *(
        GetUserCapability(
            point=26000 + slot,
            domain="number",
            key=f"simulated_load_slot_{slot + 1:02d}",
            name=f"Simulated Load Time Slot {slot + 1}",
            sample_value=100 + slot,
            expected_state=str(100 + slot),
            unit="W",
            enabled_by_default=False,
        )
        for slot in range(48)
    ),
)
