"""Base entity for the Indevolt integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IndevoltDeviceUpdateCoordinator

BATTERY_PACK_KEY = {
    1: "9032",
    2: "9051",
    3: "9070",
    4: "9165",
    5: "9218"
}


class IndevoltEntity(CoordinatorEntity[IndevoltDeviceUpdateCoordinator]):
    """Defines an Indevolt entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: IndevoltDeviceUpdateCoordinator) -> None:
        """Initialize the Indevolt entity."""
        super().__init__(coordinator)

    def device_info_main(self) -> DeviceInfo:
        entry = self.coordinator.config_entry
        sn = entry.data.get("sn")
        model = entry.data.get("device_model")

        return DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=f"{model} ({sn})",
            manufacturer="INDEVOLT",
            sw_version=entry.data.get("fw_version"),
            model=model,
            serial_number=sn,
        )

    def device_info_battery(self, pack_id: int) -> DeviceInfo:
        sn = self.coordinator.data.get(BATTERY_PACK_KEY[pack_id])

        return DeviceInfo(
            identifiers={(DOMAIN, f"battery_{pack_id}_{sn}")},
            name=f"SFA/PFA Battery Pack {pack_id} ({sn if sn != '' else None})",
            manufacturer="INDEVOLT",
            model="Battery Pack",
            serial_number=sn,
            via_device=(DOMAIN, self.coordinator.config_entry.data.get("sn")),
        )
