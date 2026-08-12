"""Creates switch entities."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import IndevoltEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class IndevoltSwitchEntityDescription(SwitchEntityDescription):
    """Class to describe a sensor entity."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]
    read_point: str = ""
    available_fn: Callable[[dict[str, Any]], bool]
    create_fn: Callable[[dict[str, Any]], bool]
    set_fn: Callable[[Any, bool], Awaitable[bool]]


SWITCHES = [
    IndevoltSwitchEntityDescription(
        key="light",
        name="Light",
        icon="mdi:led-on",
        device_class=SwitchDeviceClass.SWITCH,
        read_point="7171",
        create_fn=lambda data: "7171" in data,
        available_fn=lambda data: data.get("7171") is not None,
        is_on_fn=lambda data: data.get("7171") == 1,
        set_fn=lambda api, active: api.set_data(
            point=7265,
            value=[1] if active else [0],
        ),
    ),
    IndevoltSwitchEntityDescription(
        key="grid",
        name="Grid Charging",
        device_class=SwitchDeviceClass.OUTLET,
        read_point="2618",
        create_fn=lambda data: "2618" in data,
        available_fn=lambda data: data.get("2618") is not None,
        is_on_fn=lambda data: data.get("2618") == 1001,
        set_fn=lambda api, active: api.set_data(
            point=1143,
            value=[1] if active else [0],
        ),
    ),
    IndevoltSwitchEntityDescription(
        key="bypass",
        name="Bypass",
        device_class=SwitchDeviceClass.OUTLET,
        read_point="680",
        create_fn=lambda data: "680" in data,
        available_fn=lambda data: data.get("680") is not None,
        is_on_fn=lambda data: data.get("680") == 1,
        set_fn=lambda api, active: api.set_data(
            point=7266,
            value=[1] if active else [0],
        ),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switches."""
    if "BK1600" in entry.data.get("device_model"):
        return

    async_add_entities(
        IndevoltSwitchEntity(entry.runtime_data, description)
        for description in SWITCHES
        if description.create_fn(entry.runtime_data.data)
    )


class IndevoltSwitchEntity(IndevoltEntity, SwitchEntity):
    """Representation of a Indevolt switch."""

    def __init__(
        self, coordinator, description: IndevoltSwitchEntityDescription
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"

    @property
    def device_info(self):
        return self.device_info_main()

    @property
    def available(self) -> bool:
        return super().available and self.entity_description.available_fn(
            self.coordinator.data
        )

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self.coordinator.async_set_updated_data(
            {
                **self.coordinator.data,
                self.entity_description.read_point: True,
            }
        )
        self.async_write_ha_state()

        await self.entity_description.set_fn(self.coordinator.api, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self.coordinator.async_set_updated_data(
            {
                **self.coordinator.data,
                self.entity_description.read_point: False,
            }
        )
        self.async_write_ha_state()

        await self.entity_description.set_fn(self.coordinator.api, False)
