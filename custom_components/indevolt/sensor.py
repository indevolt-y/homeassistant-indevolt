import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory

from .capabilities import GetUserCapability
from .capabilities.runtime import (
    capabilities_for_model,
    capability_value,
    is_returned,
)
from .entity import IndevoltEntity
from .entry_config import runtime_device_model
from .sensor_descriptions.battery_pack import BATTERY_PACK_SENSORS
from .sensor_descriptions.entity_description import IndevoltSensorEntityDescription
from .sensor_descriptions.gen1 import SENSORS_GEN1
from .sensor_descriptions.gen2 import SENSORS_GEN2

_LOGGER = logging.getLogger(__name__)

P_FILE_VERSION_SENSOR = IndevoltSensorEntityDescription(
    key="p_ver",
    name="P-file Version",
    translation_key="p_file_version",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """
    Set up the sensor platform for Indevolt.

    This function is called by Home Assistant when the integration is set up.
    It creates sensor entities for each defined sensor description.
    """
    # Create an entity for each sensor description.
    device_model = runtime_device_model(entry.runtime_data)
    if "BK1600" in device_model:
        entities = [
            IndevoltSensorEntity(entry.runtime_data, description)
            for description in SENSORS_GEN1
            if entry.runtime_data.data.get(description.key) is not None
        ]
    else:
        entities = []

        for description in SENSORS_GEN2:
            if entry.runtime_data.data.get(description.key) is not None:
                entities.append(IndevoltSensorEntity(entry.runtime_data, description))

        for pack_id, sensors in BATTERY_PACK_SENSORS.items():
            for description in sensors:
                if entry.runtime_data.data.get(description.key) is not None:
                    entities.append(
                        IndevoltBatterySensorEntity(
                            entry.runtime_data, description, pack_id
                        )
                    )

    entities.extend(
        IndevoltCapabilitySensorEntity(entry.runtime_data, capability)
        for capability in capabilities_for_model(device_model)
        if capability.domain == "sensor"
        and is_returned(entry.runtime_data.data, capability)
    )
    async_add_entities(entities)

    if hass is not None:
        entry.async_create_background_task(
            hass,
            _async_add_p_file_version(entry.runtime_data, async_add_entities),
            "Load optional INDEVOLT P-file version",
        )


async def _async_add_p_file_version(coordinator, async_add_entities) -> None:
    """Add the optional Sys.GetConfig P-file version without blocking setup."""
    try:
        config = await coordinator.api.get_config()
        value = config.get("device", {}).get("p_ver")
    except Exception as err:
        _LOGGER.debug("Optional P-file version is unavailable: %s", err)
        return

    if value is None:
        return

    async_add_entities([IndevoltPFileVersionSensorEntity(coordinator, value)])


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
        return self.entity_description.value_fn(
            self.coordinator.data.get(self.entity_description.key)
        )


class IndevoltBatterySensorEntity(IndevoltEntity, SensorEntity):
    _attr_has_entity_name = True

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


class IndevoltPFileVersionSensorEntity(IndevoltEntity, SensorEntity):
    """The optional P-file version returned by Sys.GetConfig."""

    _attr_has_entity_name = True
    entity_description = P_FILE_VERSION_SENSOR

    def __init__(self, coordinator, value) -> None:
        super().__init__(coordinator)
        self._value = value
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_p_ver"

    @property
    def device_info(self):
        return self.device_info_main()

    @property
    def native_value(self):
        return self._value


class IndevoltCapabilitySensorEntity(IndevoltEntity, SensorEntity):
    """A newly documented OpenData sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, capability: GetUserCapability) -> None:
        super().__init__(coordinator)
        self.capability = capability
        self.entity_description = IndevoltSensorEntityDescription(
            key=capability.key,
            name=capability.name,
            translation_key=capability.translation_key,
            translation_placeholders=capability.translation_placeholders,
            native_unit_of_measurement=capability.unit,
            device_class=capability.device_class,
            state_class=capability.state_class,
            entity_category=capability.entity_category,
            suggested_display_precision=capability.suggested_display_precision,
            icon=capability.icon,
            options=capability.options or None,
            entity_registry_enabled_default=capability.enabled_by_default,
        )
        serial = coordinator.config_entry.unique_id
        self._attr_unique_id = capability.unique_id(serial)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        if not self.capability.scope.startswith("battery_"):
            return True
        return bool(self.device_info.get("serial_number"))

    @property
    def device_info(self):
        if self.capability.scope == "main":
            return self.device_info_main()
        pack_id = int(self.capability.scope.removeprefix("battery_"))
        return self.device_info_battery(pack_id)

    @property
    def native_value(self):
        raw_value = self.coordinator.data.get(str(self.capability.point))
        return capability_value(self.capability, raw_value)
