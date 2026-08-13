"""Complete regression contract for the two existing Indevolt Actions."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.indevolt import _register_services
from custom_components.indevolt import dr as device_registry_module
from custom_components.indevolt.const import DOMAIN


class FakeServices:
    """Store registered Action handlers."""

    def __init__(self) -> None:
        self.handlers = {}

    def async_register(self, domain, service, handler) -> None:
        self.handlers[(domain, service)] = handler


class RecordingAPI:
    """Record writes in global execution order."""

    def __init__(
        self,
        label: str,
        events: list[tuple],
        *,
        result: bool = True,
        fail_on_write: int | None = None,
    ) -> None:
        self.label = label
        self.events = events
        self.result = result
        self.fail_on_write = fail_on_write
        self.write_count = 0

    async def set_data(self, *, point, value):
        self.write_count += 1
        self.events.append((self.label, "write", point, value))
        if self.write_count == self.fail_on_write:
            raise RuntimeError(f"{self.label} write {self.write_count} failed")
        return self.result


class FakeCoordinator:
    """Expose the API and refresh behavior used by an Action."""

    def __init__(
        self,
        label: str,
        events: list[tuple],
        *,
        api_result: bool = True,
        fail_on_write: int | None = None,
        refresh_error: Exception | None = None,
    ) -> None:
        self.label = label
        self.events = events
        self.api = RecordingAPI(
            label,
            events,
            result=api_result,
            fail_on_write=fail_on_write,
        )
        self.refresh_error = refresh_error

    async def async_request_refresh(self) -> None:
        self.events.append((self.label, "refresh"))
        if self.refresh_error is not None:
            raise self.refresh_error


class FakeConfigEntries:
    """Resolve config entries by the IDs stored on devices."""

    def __init__(self, coordinators: dict[str, FakeCoordinator]) -> None:
        self.entries = {
            entry_id: SimpleNamespace(runtime_data=coordinator)
            for entry_id, coordinator in coordinators.items()
        }

    def async_get_entry(self, entry_id):
        return self.entries.get(entry_id)


class FakeRegistry:
    """Resolve device IDs to one config entry each."""

    def __init__(self, device_entries: dict[str, str]) -> None:
        self.device_entries = device_entries
        self.lookups = []

    def async_get(self, device_id):
        self.lookups.append(device_id)
        return SimpleNamespace(config_entries={self.device_entries[device_id]})


def make_hass(monkeypatch, coordinators=None):
    events = []
    coordinators = coordinators or {"entry-1": FakeCoordinator("first", events)}
    registry = FakeRegistry(
        {
            f"device-{index}": entry_id
            for index, entry_id in enumerate(coordinators, start=1)
        }
    )
    hass = SimpleNamespace(
        services=FakeServices(),
        config_entries=FakeConfigEntries(coordinators),
    )
    monkeypatch.setattr(device_registry_module, "async_get", lambda hass: registry)
    _register_services(hass)
    return hass, registry, events


def make_call(service: str, **data):
    return SimpleNamespace(service=service, data=data)


@pytest.mark.parametrize("data", [{}, {"device_id": None}, {"device_id": []}])
@pytest.mark.asyncio
async def test_action_rejects_missing_target_before_registry(monkeypatch, data) -> None:
    def unexpected_registry_access(hass):
        raise AssertionError("registry must not be accessed")

    hass = SimpleNamespace(services=FakeServices())
    monkeypatch.setattr(
        device_registry_module,
        "async_get",
        unexpected_registry_access,
    )
    _register_services(hass)
    handler = hass.services.handlers[(DOMAIN, "set_bk1600_work_mode")]

    with pytest.raises(ServiceValidationError, match="^No device selected$"):
        await handler(SimpleNamespace(service="set_bk1600_work_mode", data=data))


@pytest.mark.asyncio
async def test_action_missing_mode_keeps_key_error_before_registry(monkeypatch) -> None:
    def unexpected_registry_access(hass):
        raise AssertionError("registry must not be accessed")

    hass = SimpleNamespace(services=FakeServices())
    monkeypatch.setattr(
        device_registry_module,
        "async_get",
        unexpected_registry_access,
    )
    _register_services(hass)
    handler = hass.services.handlers[(DOMAIN, "set_bk1600_work_mode")]

    with pytest.raises(KeyError, match="mode"):
        await handler(
            make_call(
                "set_bk1600_work_mode",
                device_id=["device-1"],
            )
        )


@pytest.mark.asyncio
async def test_action_unknown_mode_fails_after_target_resolution(monkeypatch) -> None:
    hass, registry, events = make_hass(monkeypatch)
    service = "set_bk1600_work_mode"

    with pytest.raises(KeyError, match="Unknown Mode"):
        await hass.services.handlers[(DOMAIN, service)](
            make_call(
                service,
                device_id=["device-1"],
                mode="Unknown Mode",
            )
        )

    assert registry.lookups == ["device-1"]
    assert events == []


@pytest.mark.parametrize(
    ("service", "mode", "expected_writes"),
    [
        (
            "set_solidflex_powerflex_work_mode",
            "Self-Consumed Prioritized",
            [("first", "write", 47005, [1])],
        ),
        (
            "set_solidflex_powerflex_work_mode",
            "Charge/Discharge Schedule",
            [("first", "write", 47005, [5])],
        ),
        (
            "set_bk1600_work_mode",
            "Self-Consumed Prioritized",
            [("first", "write", 47005, [1])],
        ),
        (
            "set_bk1600_work_mode",
            "Charge/Discharge Schedule",
            [("first", "write", 47005, [5])],
        ),
    ],
)
@pytest.mark.asyncio
async def test_both_actions_keep_all_existing_non_realtime_modes(
    monkeypatch,
    service,
    mode,
    expected_writes,
) -> None:
    hass, registry, events = make_hass(monkeypatch)
    handler = hass.services.handlers[(DOMAIN, service)]

    await handler(
        make_call(
            service,
            device_id=["device-1"],
            mode=mode,
            state="Discharging",
            power=999_999,
            soc=-1,
        )
    )

    assert registry.lookups == ["device-1"]
    assert events == [*expected_writes, ("first", "refresh")]


@pytest.mark.parametrize(
    ("state", "expected_state"),
    [
        ("Standby", 0),
        ("Charging", 1),
        ("Discharging", 2),
        ("Unknown State", None),
    ],
)
@pytest.mark.asyncio
async def test_realtime_action_keeps_state_mapping(
    monkeypatch, state, expected_state
) -> None:
    hass, _registry, events = make_hass(monkeypatch)
    service = "set_solidflex_powerflex_work_mode"
    handler = hass.services.handlers[(DOMAIN, service)]

    await handler(
        make_call(
            service,
            device_id=["device-1"],
            mode="Real-Time Control",
            state=state,
            power=1200,
            soc=80,
        )
    )

    assert events == [
        ("first", "write", 47005, [4]),
        ("first", "write", 47015, [expected_state, 1200, 80]),
        ("first", "refresh"),
    ]


@pytest.mark.asyncio
async def test_realtime_action_keeps_optional_defaults(monkeypatch) -> None:
    hass, _registry, events = make_hass(monkeypatch)
    service = "set_bk1600_work_mode"

    await hass.services.handlers[(DOMAIN, service)](
        make_call(
            service,
            device_id=["device-1"],
            mode="Real-Time Control",
        )
    )

    assert events == [
        ("first", "write", 47005, [4]),
        ("first", "write", 47015, [0, 0, 5]),
        ("first", "refresh"),
    ]


@pytest.mark.parametrize(
    ("service", "mode", "power", "raises"),
    [
        ("set_solidflex_powerflex_work_mode", "Real-Time Control", 10_800, False),
        ("set_solidflex_powerflex_work_mode", "Real-Time Control", 10_801, True),
        (
            "set_solidflex_powerflex_work_mode",
            "Self-Consumed Prioritized",
            10_801,
            False,
        ),
        ("set_bk1600_work_mode", "Real-Time Control", 10_801, False),
    ],
)
@pytest.mark.asyncio
async def test_power_limit_scope_is_unchanged(
    monkeypatch,
    service,
    mode,
    power,
    raises,
) -> None:
    hass, registry, events = make_hass(monkeypatch)
    handler = hass.services.handlers[(DOMAIN, service)]
    call = make_call(
        service,
        device_id=["device-1"],
        mode=mode,
        power=power,
    )

    if raises:
        with pytest.raises(ServiceValidationError, match="10800 W"):
            await handler(call)
        assert registry.lookups == []
        assert events == []
    else:
        await handler(call)
        assert registry.lookups == ["device-1"]
        assert events[-1] == ("first", "refresh")


@pytest.mark.asyncio
async def test_action_processes_multiple_targets_in_input_order(monkeypatch) -> None:
    events = []
    coordinators = {
        "entry-1": FakeCoordinator("first", events),
        "entry-2": FakeCoordinator("second", events),
    }
    hass, registry, _ = make_hass(monkeypatch, coordinators)
    service = "set_solidflex_powerflex_work_mode"

    await hass.services.handlers[(DOMAIN, service)](
        make_call(
            service,
            device_id=["device-2", "device-1"],
            mode="Real-Time Control",
            state="Charging",
            power=800,
            soc=70,
        )
    )

    assert registry.lookups == ["device-2", "device-1"]
    assert events == [
        ("second", "write", 47005, [4]),
        ("second", "write", 47015, [1, 800, 70]),
        ("second", "refresh"),
        ("first", "write", 47005, [4]),
        ("first", "write", 47015, [1, 800, 70]),
        ("first", "refresh"),
    ]


@pytest.mark.asyncio
async def test_false_write_result_still_refreshes(monkeypatch) -> None:
    events = []
    coordinators = {
        "entry-1": FakeCoordinator("first", events, api_result=False),
    }
    hass, _registry, _ = make_hass(monkeypatch, coordinators)
    service = "set_bk1600_work_mode"

    await hass.services.handlers[(DOMAIN, service)](
        make_call(
            service,
            device_id=["device-1"],
            mode="Self-Consumed Prioritized",
        )
    )

    assert events == [
        ("first", "write", 47005, [1]),
        ("first", "refresh"),
    ]


@pytest.mark.parametrize(
    ("fail_on_write", "expected_events"),
    [
        (1, [("first", "write", 47005, [4])]),
        (
            2,
            [
                ("first", "write", 47005, [4]),
                ("first", "write", 47015, [1, 800, 70]),
            ],
        ),
    ],
)
@pytest.mark.asyncio
async def test_write_exception_stops_before_refresh(
    monkeypatch,
    fail_on_write,
    expected_events,
) -> None:
    events = []
    coordinators = {
        "entry-1": FakeCoordinator(
            "first",
            events,
            fail_on_write=fail_on_write,
        ),
    }
    hass, _registry, _ = make_hass(monkeypatch, coordinators)
    service = "set_solidflex_powerflex_work_mode"

    with pytest.raises(RuntimeError, match=f"write {fail_on_write} failed"):
        await hass.services.handlers[(DOMAIN, service)](
            make_call(
                service,
                device_id=["device-1"],
                mode="Real-Time Control",
                state="Charging",
                power=800,
                soc=70,
            )
        )

    assert events == expected_events


@pytest.mark.asyncio
async def test_refresh_exception_prevents_later_targets(monkeypatch) -> None:
    events = []
    coordinators = {
        "entry-1": FakeCoordinator(
            "first",
            events,
            refresh_error=RuntimeError("refresh failed"),
        ),
        "entry-2": FakeCoordinator("second", events),
    }
    hass, registry, _ = make_hass(monkeypatch, coordinators)
    service = "set_bk1600_work_mode"

    with pytest.raises(RuntimeError, match="^refresh failed$"):
        await hass.services.handlers[(DOMAIN, service)](
            make_call(
                service,
                device_id=["device-1", "device-2"],
                mode="Self-Consumed Prioritized",
            )
        )

    assert registry.lookups == ["device-1"]
    assert events == [
        ("first", "write", 47005, [1]),
        ("first", "refresh"),
    ]
