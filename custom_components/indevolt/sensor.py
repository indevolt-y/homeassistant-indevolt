from homeassistant.components.sensor import SensorEntity

from .entity import IndevoltEntity
from .sensor_descriptions.battery_pack import BATTERY_PACK_SENSORS
from .sensor_descriptions.entity_description import IndevoltSensorEntityDescription
from .sensor_descriptions.gen1 import SENSORS_GEN1
from .sensor_descriptions.gen2 import SENSORS_GEN2


async def async_setup_entry(hass, entry, async_add_entities):
    """
    Set up the sensor platform for Indevolt.
    
    This function is called by Home Assistant when the integration is set up.
    It creates sensor entities for each defined sensor description.
    """
    # Create an entity for each sensor description.
    if "BK1600" in entry.data.get("device_model"):
        async_add_entities(
            IndevoltSensorEntity(entry.runtime_data, description)
            for description in SENSORS_GEN1
            if entry.runtime_data.data.get(description.key) is not None
        )
    else:
        entities = []

        for description in SENSORS_GEN2:
            if entry.runtime_data.data.get(description.key) is not None:
                entities.append(IndevoltSensorEntity(entry.runtime_data, description))

        for pack_id, sensors in BATTERY_PACK_SENSORS.items():
            for description in sensors:
                if entry.runtime_data.data.get(description.key) is not None:
                    entities.append(IndevoltBatterySensorEntity(entry.runtime_data, description, pack_id))

        async_add_entities(entities)

class IndevoltSensorEntity(IndevoltEntity, SensorEntity):
    """Represents a sensor entity for Indevolt devices."""

    # Enable entity name as the only name (without device name prefix)
    _attr_has_entity_name = True

    def __init__(self, coordinator, description: IndevoltSensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"

    @property
    def device_info(self):
        return self.device_info_main()

    @property
    def native_value(self):
        """Return the current value of the sensor in its native unit."""    
        return self.entity_description.value_fn(self.coordinator.data.get(self.entity_description.key))


class IndevoltBatterySensorEntity(IndevoltEntity, SensorEntity):
    def __init__(self, coordinator, description, pack_id: int):
        super().__init__(coordinator)
        self.entity_description = description
        self.pack_id = pack_id
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}_battery_{pack_id}_{description.key}"
        )

    @property
    def available(self):
        return bool(self.device_info.get("serial_number"))

    @property
    def device_info(self):
        return self.device_info_battery(self.pack_id)

    @property
    def native_value(self):
        return self.entity_description.value_fn(
            self.coordinator.data.get(self.entity_description.key)
        )
