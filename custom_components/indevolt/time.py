"""Time entities for documented OpenData controls."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .capabilities import SetUserCapability
from .capabilities.runtime import (
    async_write_control,
    controls_for_model,
    decode_time,
    encode_time,
    is_control_returned,
)
from .entity import IndevoltEntity
from .entry_config import runtime_device_model


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up returned time controls for the historical non-BK route."""
    capabilities = controls_for_model(runtime_device_model(entry.runtime_data))
    async_add_entities(
        IndevoltCapabilityTimeEntity(entry.runtime_data, capability)
        for capability in capabilities
        if capability.entity_domain == "time"
        and is_control_returned(entry.runtime_data.data, capability)
    )


class IndevoltCapabilityTimeEntity(IndevoltEntity, TimeEntity):
    """A new OpenData time control with a matching device readback."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, capability: SetUserCapability) -> None:
        super().__init__(coordinator)
        assert capability.key is not None
        assert capability.translation_key is not None
        assert capability.read_point is not None
        self.capability = capability
        self.entity_description = TimeEntityDescription(
            key=capability.key,
            name=capability.name,
            translation_key=capability.translation_key,
            translation_placeholders=capability.translation_placeholders,
            entity_category=capability.entity_category,
            icon=capability.icon,
            entity_registry_enabled_default=capability.enabled_by_default,
        )
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{capability.key}"

    @property
    def device_info(self):
        return self.device_info_main()

    @property
    def native_value(self) -> time | None:
        return decode_time(self.coordinator.data.get(str(self.capability.read_point)))

    async def async_set_value(self, value: time) -> None:
        await async_write_control(
            self.coordinator,
            self.capability,
            encode_time(value),
        )
