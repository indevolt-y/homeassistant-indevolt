"""SolidFlex2000 number, select, switch, and Action contracts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.indevolt import _register_services
from custom_components.indevolt import dr as device_registry_module
from custom_components.indevolt.number import NUMBERS_GEN2, IndevoltNumberEntity
from custom_components.indevolt.select import SELECTS_GEN2, IndevoltSelectEntity
from custom_components.indevolt.switch import SWITCHES, IndevoltSwitchEntity

MODEL = "SolidFlex/PowerFlex2000"


class FakeAPI:
    """Record SolidFlex2000 control writes."""

    def __init__(self) -> None:
        self.writes = []

    async def set_data(self, *, point, value):
        self.writes.append((point, value))
        return True


class FakeCoordinator:
    """Provide SolidFlex2000 control state and refresh observation."""

    def __init__(self, data=None) -> None:
        self.api = FakeAPI()
        self.config_entry = SimpleNamespace(
            unique_id="solidflex2000-entry",
            data={
                "sn": "SOLIDFLEX2000-SN",
                "device_model": MODEL,
                "fw_version": "2.0.0",
            },
        )
        self.data = dict(data or {})
        self.last_update_success = True
        self.request_refreshes = 0
        self.refreshes = 0
        self.updated_data = []

    async def async_request_refresh(self) -> None:
        self.request_refreshes += 1

    async def async_refresh(self) -> None:
        self.refreshes += 1

    def async_set_updated_data(self, data) -> None:
        self.data = data
        self.updated_data.append(dict(data))


def make_number_entity(coordinator, description):
    entity = object.__new__(IndevoltNumberEntity)
    entity.coordinator = coordinator
    entity.entity_description = description
    return entity


@pytest.mark.asyncio
@pytest.mark.parametrize("power", [2_400, 2_401, 4_800, 7_200, 10_800])
async def test_solidflex2000_number_accepts_supported_power(power) -> None:
    coordinator = FakeCoordinator()
    description = next(item for item in NUMBERS_GEN2 if item.key == "power_setting")
    entity = make_number_entity(coordinator, description)

    await entity.async_set_native_value(power)

    assert coordinator.api.writes == [(47016, [power])]
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_solidflex2000_number_rejects_10801_before_write() -> None:
    coordinator = FakeCoordinator()
    description = next(item for item in NUMBERS_GEN2 if item.key == "power_setting")
    entity = make_number_entity(coordinator, description)

    with pytest.raises(ServiceValidationError, match="10800 W"):
        await entity.async_set_native_value(10_801)

    assert coordinator.api.writes == []
    assert coordinator.refreshes == 0


@pytest.mark.asyncio
async def test_solidflex2000_select_ignores_unknown_option() -> None:
    coordinator = FakeCoordinator({"7101": 1})
    entity = IndevoltSelectEntity(coordinator, SELECTS_GEN2[0])

    await entity.async_select_option("Unknown Mode")

    assert coordinator.api.writes == []
    assert coordinator.refreshes == 0
    assert entity.current_option == "Self-Consumed Prioritized"


@pytest.mark.asyncio
async def test_solidflex2000_select_maps_existing_option() -> None:
    coordinator = FakeCoordinator({"7101": 1})
    entity = IndevoltSelectEntity(coordinator, SELECTS_GEN2[0])

    await entity.async_select_option("Real-Time Control")

    assert coordinator.api.writes == [(47005, [4])]
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_solidflex2000_switch_optimistically_updates_then_writes(
    monkeypatch,
) -> None:
    coordinator = FakeCoordinator({"7171": 0})
    description = next(item for item in SWITCHES if item.key == "light")
    entity = IndevoltSwitchEntity(coordinator, description)
    written_states = []
    monkeypatch.setattr(
        entity,
        "async_write_ha_state",
        lambda: written_states.append(entity.is_on),
    )

    await entity.async_turn_on()
    await entity.async_turn_off()

    assert coordinator.updated_data == [{"7171": True}, {"7171": False}]
    assert written_states == [True, False]
    assert coordinator.api.writes == [(7265, [1]), (7265, [0])]


def test_solidflex2000_switch_with_null_point_is_unavailable() -> None:
    coordinator = FakeCoordinator({"2618": None})
    description = next(item for item in SWITCHES if item.key == "grid")
    entity = IndevoltSwitchEntity(coordinator, description)

    assert description.create_fn(coordinator.data) is True
    assert entity.available is False


class FakeServices:
    """Store SolidFlex2000 service handlers."""

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


def make_hass(coordinator):
    return SimpleNamespace(
        services=FakeServices(),
        config_entries=FakeConfigEntries(coordinator),
    )


def service_call(power: int):
    return SimpleNamespace(
        service="set_solidflex_powerflex_work_mode",
        data={
            "device_id": ["device-id"],
            "mode": "Real-Time Control",
            "state": "Charging",
            "power": power,
            "soc": 80,
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("power", [2_400, 2_401, 4_800, 7_200, 10_800])
async def test_solidflex2000_action_accepts_supported_power(
    monkeypatch,
    power,
) -> None:
    coordinator = FakeCoordinator()
    hass = make_hass(coordinator)
    monkeypatch.setattr(
        device_registry_module, "async_get", lambda hass: FakeRegistry()
    )
    _register_services(hass)

    await hass.services.handlers[("indevolt", "set_solidflex_powerflex_work_mode")](
        service_call(power)
    )

    assert coordinator.api.writes == [(47005, [4]), (47015, [1, power, 80])]
    assert coordinator.request_refreshes == 1


@pytest.mark.asyncio
async def test_solidflex2000_action_rejects_10801_before_registry_or_api(
    monkeypatch,
) -> None:
    coordinator = FakeCoordinator()
    hass = make_hass(coordinator)

    def unexpected_registry_access(hass):
        raise AssertionError("device registry must not be accessed")

    monkeypatch.setattr(device_registry_module, "async_get", unexpected_registry_access)
    _register_services(hass)

    with pytest.raises(ServiceValidationError, match="10800 W"):
        await hass.services.handlers[("indevolt", "set_solidflex_powerflex_work_mode")](
            service_call(10_801)
        )

    assert coordinator.api.writes == []
    assert coordinator.request_refreshes == 0
