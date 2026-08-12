from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.helpers.entity import EntityCategory

from .entity_description import IndevoltSensorEntityDescription

SENSORS_GEN1: Final = (
    IndevoltSensorEntityDescription(
        key="1664",
        name="DC Input Power1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="1665",
        name="DC Input Power2",
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
    IndevoltSensorEntityDescription(
        key="1502",
        name="Daily Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="1505",
        name="Cumulative Production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda value: value * 0.001
    ),
    IndevoltSensorEntityDescription(
        key="2101",
        name="Total AC Input Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="2107",
        name="Total AC Input Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING
    ),
    IndevoltSensorEntityDescription(
        key="1501",
        name="Total DC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6000",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6002",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="6105",
        name="Emergency power supply",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT
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
    IndevoltSensorEntityDescription(
        key="21028",
        name="Meter Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    IndevoltSensorEntityDescription(
        key="7101",
        name="Working mode",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: {
            0: "Outdoor Portable",
            1: "Self-consumed Prioritized",
            4: "Real-Time Control",
            5: "Charge/Discharge Schedule"
        }.get(value)
    ),
    IndevoltSensorEntityDescription(
        key="6001",
        name="Battery Charge/Discharge State",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: {
            1000: "Static",
            1001: "Charging",
            1002: "Discharging"
        }.get(value)
    ),
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
)
