from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import IndevoltDeviceUpdateCoordinator
from .entity import IndevoltEntity


@dataclass(frozen=True, kw_only=True)
class IndevoltSelectDescription(SelectEntityDescription):
    key: str
    name: str
    icon: str

    value_fn: Callable[[IndevoltDeviceUpdateCoordinator], int | None]
    set_fn: Callable[[IndevoltDeviceUpdateCoordinator, int], Awaitable[bool]]

    options_map: dict[int, str]
    read_point: str = ""
    entity_category: EntityCategory = EntityCategory.CONFIG


SELECTS_GEN2: tuple[IndevoltSelectDescription, ...] = (
    IndevoltSelectDescription(
        key="work_mode",
        translation_key="work_mode",
        name="Work Mode",
        icon="mdi:cog",
        options_map={
            1: "Self-Consumed Prioritized",
            4: "Real-Time Control",
            5: "Charge/Discharge Schedule",
        },
        read_point="7101",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data.get("7101"),
        set_fn=lambda c, value: c.api.set_data(point=47005, value=[value]),
    ),
    IndevoltSelectDescription(
        key="state_setting",
        translation_key="real_time_control_state",
        name="State (Real-time control)",
        icon="mdi:cog",
        options_map={0: "Standby", 1: "Charging", 2: "Discharging"},
        read_point="6001",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: (
            data.get("6001") - 1000 if data.get("6001") is not None else None
        ),
        set_fn=lambda c, value: c.api.set_data(point=47015, value=[value]),
    ),
    IndevoltSelectDescription(
        key="load_setting",
        translation_key="load_setting",
        name="Load Setting",
        icon="mdi:cog",
        options_map={1: "Smart Plug", 2: "Meter", 3: "Key Load", 4: "Custom"},
        value_fn=lambda data: None,
        set_fn=lambda c, value: c.api.set_data(point=1, value=[value]),
    ),
)

SELECTS_GEN1: tuple[IndevoltSelectDescription, ...] = (
    IndevoltSelectDescription(
        key="state_setting",
        translation_key="real_time_control_state",
        name="State (Real-time control)",
        icon="mdi:cog",
        options_map={0: "Standby", 1: "Charging", 2: "Discharging"},
        read_point="6001",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data.get("6001") - 1000,
        set_fn=lambda c, value: c.api.set_data(point=47015, value=[value]),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: IndevoltDeviceUpdateCoordinator = entry.runtime_data

    if "BK1600" in entry.data.get("device_model"):
        async_add_entities(
            IndevoltSelectEntity(coordinator, description)
            for description in SELECTS_GEN1
        )
    else:
        async_add_entities(
            IndevoltSelectEntity(coordinator, description)
            for description in SELECTS_GEN2
        )


class IndevoltSelectEntity(IndevoltEntity, SelectEntity):
    """Indevolt Select Entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IndevoltDeviceUpdateCoordinator,
        description: IndevoltSelectDescription,
    ) -> None:
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_options = list(description.options_map.values())
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"

    @property
    def device_info(self):
        return self.device_info_main()

    async def async_select_option(self, option: str) -> None:
        reverse_map = {v: k for k, v in self.entity_description.options_map.items()}
        value = reverse_map.get(option)

        if value is None:
            return

        self._attr_current_option = option
        await self.entity_description.set_fn(self.coordinator, value)
        await self.coordinator.async_refresh()

    @property
    def current_option(self) -> str | None:
        """Return the current option as a string for HA UI."""

        value = self.entity_description.value_fn(self.coordinator.data)

        if value is None:
            return None

        return self.entity_description.options_map.get(value)
