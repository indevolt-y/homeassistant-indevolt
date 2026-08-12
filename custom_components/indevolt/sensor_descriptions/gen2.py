from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from .entity_description import (
    IndevoltSensorEntityDescription,
    format_firmware_version,
)

SENSORS_GEN2: Final = (
    # Firmware Version Information
    IndevoltSensorEntityDescription(
        key="1118",	
        name="Firmware PG2000Series EMS",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value)
    ),
    IndevoltSensorEntityDescription(
        key="1109",	
        name="Firmware PG2000Series BMS-MB",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value)
    ),
    IndevoltSensorEntityDescription(
        key="1119",	
        name="Firmware PG2000Series PCS",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value)
    ),
    IndevoltSensorEntityDescription(
        key="1120",	
        name="Firmware PG2000Series DCDC",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value)
    ),
    # System Operating Information
    IndevoltSensorEntityDescription(
        key="142",
        name="Rated Capacity",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="2101",
        name="Total AC Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="2108",
        name="Total AC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    # Cluster Information
    IndevoltSensorEntityDescription(
        key="606",
        name="Master-Slave Identification",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: {
            "1000": "Master",
            "1001": "Slave",
            "1002": "None"
        }.get(value)
    ),
    # Bypass Power
    IndevoltSensorEntityDescription(
        key="667",
        name="Bypass Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    # Electrical Energy Information
    IndevoltSensorEntityDescription(
        key="2107",
        name="Total AC Input Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="2104",
        name="Total AC Output Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="2105",
        name="Off-grid Output Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="11034",
        name="Bypass Input Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="1502",
        name="Daily Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6004",
        name="Battery Daily Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6005",
        name="Battery Daily Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6006",
        name="Battery Total Charging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="6007",
        name="Battery Total Discharging Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    # Electricity Meter Status
    IndevoltSensorEntityDescription(
        key="7120",
        name="Meter Connection Status",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: {
            1000: "ON",
            1001: "OFF"
        }.get(value)
    ),
    IndevoltSensorEntityDescription(
        key="11016",
        name="Meter Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    # Grid Information
    IndevoltSensorEntityDescription(
        key="2600",
        name="Grid Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="2612",
        name="Grid Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Battery Pack Operating Parameters
    IndevoltSensorEntityDescription(
        key="6000",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6002",
        name="Battery SOC Total",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="9008",
        name="Battery SN-MB",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    IndevoltSensorEntityDescription(
        key="9000",
        name="Battery SOC-MB",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="9004",
        name="Battery V-MB",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9013",
        name="Battery I-MB",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9012",
        name="Battery Temp-MB",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9009",
        name="Battery Cell1 V-MB",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9011",
        name="Battery Cell2 V-MB",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # PV Operating Parameters
    IndevoltSensorEntityDescription(
        key="1501",
        name="Total DC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1632",
        name="DC Input Current 1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1600",
        name="DC Input Voltage 1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1664",
        name="DC Input Power 1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1633",
        name="DC Input Current 2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1601",
        name="DC Input Voltage 2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1665",
        name="DC Input Power 2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1634",
        name="DC Input Current 3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1602",
        name="DC Input Voltage 3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1666",
        name="DC Input Power 3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1635",
        name="DC Input Current 4",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1603",
        name="DC Input Voltage 4",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="1667",
        name="DC Input Power 4",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    )
)
