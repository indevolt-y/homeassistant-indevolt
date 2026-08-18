"""Binary sensor entities for documented OpenData points."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .capabilities import GetUserCapability
from .capabilities.runtime import (
    capabilities_for_model,
    capability_value,
    is_returned,
)
from .entity import IndevoltEntity
from .entry_config import runtime_device_model


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up returned binary values without changing existing platforms."""
    capabilities = capabilities_for_model(runtime_device_model(entry.runtime_data))
    async_add_entities(
        IndevoltCapabilityBinarySensorEntity(entry.runtime_data, capability)
        for capability in capabilities
        if capability.domain == "binary_sensor"
        and is_returned(entry.runtime_data.data, capability)
    )


class IndevoltCapabilityBinarySensorEntity(IndevoltEntity, BinarySensorEntity):
    """One newly documented OpenData binary sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, capability: GetUserCapability) -> None:
        super().__init__(coordinator)
        self.capability = capability
        self.entity_description = BinarySensorEntityDescription(
            key=capability.key,
            name=capability.name,
            translation_key=capability.translation_key,
            translation_placeholders=capability.translation_placeholders,
            device_class=capability.device_class,
            entity_category=capability.entity_category,
            icon=capability.icon,
            entity_registry_enabled_default=capability.enabled_by_default,
        )
        self._attr_unique_id = capability.unique_id(coordinator.config_entry.unique_id)

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
    def is_on(self) -> bool | None:
        raw_value = self.coordinator.data.get(str(self.capability.point))
        return capability_value(self.capability, raw_value)
