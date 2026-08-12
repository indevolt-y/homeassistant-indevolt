"""BK1600Ultra number, select, and Action contracts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.indevolt import _register_services
from custom_components.indevolt import dr as device_registry_module
from custom_components.indevolt.number import NUMBERS_GEN1, IndevoltNumberEntity
from custom_components.indevolt.select import SELECTS_GEN1, IndevoltSelectEntity

MODEL = "BK1600/BK1600Ultra"


class FakeAPI:
    """Record BK1600Ultra control writes."""

    def __init__(self) -> None:
        self.writes = []

    async def set_data(self, *, point, value):
        self.writes.append((point, value))
        return True


class FakeCoordinator:
    """Provide BK1600Ultra control state and refresh observation."""

    def __init__(self, data=None) -> None:
        self.api = FakeAPI()
        self.config_entry = SimpleNamespace(
            unique_id="bk1600-ultra-entry",
            data={
                "sn": "BK1600-ULTRA-SN",
                "device_model": MODEL,
                "fw_version": "2.0.0",
            },
        )
        self.data = dict(data or {})
        self.request_refreshes = 0
        self.refreshes = 0

    async def async_request_refresh(self) -> None:
        self.request_refreshes += 1

    async def async_refresh(self) -> None:
        self.refreshes += 1


def make_number_entity(coordinator, description):
    entity = object.__new__(IndevoltNumberEntity)
    entity.coordinator = coordinator
    entity.entity_description = description
    return entity


@pytest.mark.asyncio
@pytest.mark.parametrize(("state", "maximum"), [(1001, 1_200), (1000, 800)])
async def test_bk1600_ultra_number_keeps_dynamic_boundary(state, maximum) -> None:
    coordinator = FakeCoordinator({"6001": state})
    description = next(item for item in NUMBERS_GEN1 if item.key == "power_setting")
    entity = make_number_entity(coordinator, description)

    assert entity.native_max_value == maximum

    requested_value = float(maximum)
    await entity.async_set_native_value(requested_value)

    assert coordinator.api.writes == [(47016, [requested_value])]
    assert type(coordinator.api.writes[0][1][0]) is float
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_bk1600_ultra_select_ignores_unknown_option() -> None:
    coordinator = FakeCoordinator({"6001": 1001})
    entity = IndevoltSelectEntity(coordinator, SELECTS_GEN1[0])

    await entity.async_select_option("Unknown State")

    assert coordinator.api.writes == []
    assert coordinator.refreshes == 0
    assert entity.current_option == "Charging"


@pytest.mark.asyncio
async def test_bk1600_ultra_select_maps_existing_option() -> None:
    coordinator = FakeCoordinator({"6001": 1001})
    entity = IndevoltSelectEntity(coordinator, SELECTS_GEN1[0])

    await entity.async_select_option("Discharging")

    assert coordinator.api.writes == [(47015, [2])]
    assert coordinator.refreshes == 1


class FakeServices:
    """Store BK1600Ultra service handlers."""

    def __init__(self) -> None:
        self.handlers = {}

    def async_register(self, domain, service, handler) -> None:
        self.handlers[(domain, service)] = handler


class FakeConfigEntries:
    def __init__(self, coordinator) -> None:
        self.entry = SimpleNamespace(runtime_data=coordinator)

    def async_get_entry(self, entry_id):
        assert entry_id == "entry-id"
        return self.entry


class FakeRegistry:
    def async_get(self, device_id):
        assert device_id == "device-id"
        return SimpleNamespace(config_entries={"entry-id"})


@pytest.mark.asyncio
async def test_bk1600_ultra_action_keeps_existing_selector_maximum(monkeypatch) -> None:
    coordinator = FakeCoordinator()
    hass = SimpleNamespace(
        services=FakeServices(),
        config_entries=FakeConfigEntries(coordinator),
    )
    monkeypatch.setattr(
        device_registry_module, "async_get", lambda hass: FakeRegistry()
    )
    _register_services(hass)
    call = SimpleNamespace(
        service="set_bk1600_work_mode",
        data={
            "device_id": ["device-id"],
            "mode": "Real-Time Control",
            "state": "Charging",
            "power": 1_200,
            "soc": 80,
        },
    )

    await hass.services.handlers[("indevolt", "set_bk1600_work_mode")](call)

    assert coordinator.api.writes == [(47005, [4]), (47015, [1, 1_200, 80])]
    assert coordinator.request_refreshes == 1
