from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTemperature,
)

from .entity_description import (
    IndevoltSensorEntityDescription,
    format_firmware_version,
)

BATTERY_PACK1_SENSORS = {
    IndevoltSensorEntityDescription(
        key="1136",
        name="Firmware SFA/PFA DCDC1",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="1137",
        name="Firmware SFA/PFA BMS1",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="9016",
        name="Battery SOC-Pack1",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9020",
        name="Battery V-Pack1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="19173",
        name="Battery I-Pack1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9030",
        name="Battery Temp-Pack1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9021",
        name="Battery Cell1 V-Pack1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9023",
        name="Battery Cell2 V-Pack1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

BATTERY_PACK2_SENSORS = {
    IndevoltSensorEntityDescription(
        key="1138",
        name="Firmware SFA/PFA DCDC2",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="1139",
        name="Firmware SFA/PFA BMS2",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="9035",
        name="Battery SOC-Pack2",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9039",
        name="Battery V-Pack2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="19174",
        name="Battery I-Pack2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9049",
        name="Battery Temp-Pack2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9040",
        name="Battery Cell1 V-Pack2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9042",
        name="Battery Cell2 V-Pack2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

BATTERY_PACK3_SENSORS = {
    IndevoltSensorEntityDescription(
        key="1140",
        name="Firmware SFA/PFA DCDC3",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="1141",
        name="Firmware SFA/PFA BMS3",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="9054",
        name="Battery SOC-Pack3",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9058",
        name="Battery V-Pack3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="19175",
        name="Battery I-Pack3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9068",
        name="Battery Temp-Pack3",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9059",
        name="Battery Cell1 V-Pack3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9061",
        name="Battery Cell2 V-Pack3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

BATTERY_PACK4_SENSORS = {
    IndevoltSensorEntityDescription(
        key="1142",
        name="Firmware SFA/PFA DCDC4",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="1143",
        name="Firmware SFA/PFA BMS4",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="9149",
        name="Battery SOC-Pack4",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9153",
        name="Battery V-Pack4",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="19176",
        name="Battery I-Pack4",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9163",
        name="Battery Temp-Pack4",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9154",
        name="Battery Cell1 V-Pack4",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9156",
        name="Battery Cell2 V-Pack4",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

BATTERY_PACK5_SENSORS = {
    IndevoltSensorEntityDescription(
        key="1098",
        name="Firmware SFA/PFA DCDC5",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="1099",
        name="Firmware SFA/PFA BMS5",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: format_firmware_version(version=value),
    ),
    IndevoltSensorEntityDescription(
        key="9202",
        name="Battery SOC-Pack5",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9206",
        name="Battery V-Pack5",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="19177",
        name="Battery I-Pack5",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9216",
        name="Battery Temp-Pack5",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9219",
        name="Battery Cell1 V-Pack5",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IndevoltSensorEntityDescription(
        key="9222",
        name="Battery Cell2 V-Pack5",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

BATTERY_PACK_SENSORS = {
    1: BATTERY_PACK1_SENSORS,
    2: BATTERY_PACK2_SENSORS,
    3: BATTERY_PACK3_SENSORS,
    4: BATTERY_PACK4_SENSORS,
    5: BATTERY_PACK5_SENSORS,
}
