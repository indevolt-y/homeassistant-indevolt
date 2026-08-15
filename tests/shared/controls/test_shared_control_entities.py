"""Complete runtime regression contract for Number, Select, and Switch."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.indevolt import number as number_platform
from custom_components.indevolt import select as select_platform
from custom_components.indevolt import switch as switch_platform
from custom_components.indevolt.number import (
    NUMBERS_GEN1,
    NUMBERS_GEN2,
    IndevoltNumberEntity,
)
from custom_components.indevolt.select import (
    SELECTS_GEN1,
    SELECTS_GEN2,
    IndevoltSelectEntity,
)
from custom_components.indevolt.switch import SWITCHES, IndevoltSwitchEntity


class RecordingAPI:
    """Record writes and expose result/error behavior."""

    def __init__(self, *, result: bool = True, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.writes = []

    async def set_data(self, *, point, value):
        self.writes.append((point, value))
        if self.error is not None:
            raise self.error
        return self.result


class FakeCoordinator:
    """Provide all coordinator behavior used by control entities."""

    def __init__(self, model: str, data=None, api=None) -> None:
        self.api = api or RecordingAPI()
        self.config_entry = SimpleNamespace(
            unique_id="control-entry",
            data={
                "sn": "CONTROL-SN",
                "device_model": model,
                "fw_version": "1.2.3",
            },
        )
        self.data = dict(data or {})
        self.last_update_success = True
        self.refreshes = 0
        self.updated_data = []

    async def async_refresh(self) -> None:
        self.refreshes += 1

    def async_set_updated_data(self, data) -> None:
        self.data = data
        self.updated_data.append(dict(data))


def _entry(coordinator):
    return SimpleNamespace(
        data=coordinator.config_entry.data,
        runtime_data=coordinator,
    )


@pytest.mark.parametrize(
    ("model", "expected_keys"),
    [
        (
            "BK1600/BK1600Ultra",
            ["power_setting", "soc_setting"],
        ),
        (
            "prefix-BK1600-suffix",
            ["power_setting", "soc_setting"],
        ),
        (
            "SolidFlex/PowerFlex2000",
            [
                "backup_soc",
                "inverter_input_limit",
                "max_output_power",
                "feed_in_power_limit",
                "power_setting",
                "soc_setting",
            ],
        ),
        (
            "FutureModel",
            [
                "backup_soc",
                "inverter_input_limit",
                "max_output_power",
                "feed_in_power_limit",
                "power_setting",
                "soc_setting",
            ],
        ),
    ],
)
@pytest.mark.asyncio
async def test_number_setup_keeps_exact_route_and_definition_order(
    monkeypatch,
    model,
    expected_keys,
) -> None:
    coordinator = FakeCoordinator(model)
    added = []
    monkeypatch.setattr(
        number_platform,
        "IndevoltNumberEntity",
        lambda coordinator, description: description.key,
    )

    await number_platform.async_setup_entry(
        None,
        _entry(coordinator),
        lambda entities: added.extend(entities),
    )

    assert added == expected_keys


@pytest.mark.parametrize(
    ("model", "descriptions", "state", "expected"),
    [
        (
            "SolidFlex/PowerFlex2000",
            NUMBERS_GEN2,
            {},
            {
                "backup_soc": 100,
                "inverter_input_limit": 2400,
                "max_output_power": 2400,
                "feed_in_power_limit": 2400,
                "power_setting": 10_800,
                "soc_setting": 100,
            },
        ),
        (
            "BK1600/BK1600Ultra",
            NUMBERS_GEN1,
            {"6001": 1001},
            {"power_setting": 1200, "soc_setting": 100},
        ),
        (
            "BK1600/BK1600Ultra",
            NUMBERS_GEN1,
            {"6001": 1000},
            {"power_setting": 800, "soc_setting": 100},
        ),
        (
            "BK1600/BK1600Ultra",
            NUMBERS_GEN1,
            {},
            {"power_setting": 800, "soc_setting": 100},
        ),
    ],
)
def test_number_native_max_value_keeps_every_model_branch(
    model,
    descriptions,
    state,
    expected,
) -> None:
    coordinator = FakeCoordinator(model, state)

    assert {
        description.key: IndevoltNumberEntity(
            coordinator,
            description,
        ).native_max_value
        for description in descriptions
    } == expected


def test_number_native_value_reads_latest_coordinator_data() -> None:
    coordinator = FakeCoordinator(
        "SolidFlex/PowerFlex2000",
        {"6105": 50, "11009": 1000, "11011": 1100, "11010": 1200},
    )
    entities = {
        description.key: IndevoltNumberEntity(coordinator, description)
        for description in NUMBERS_GEN2
    }

    assert {key: entity.native_value for key, entity in entities.items()} == {
        "backup_soc": 50,
        "inverter_input_limit": 1000,
        "max_output_power": 1100,
        "feed_in_power_limit": 1200,
        "power_setting": None,
        "soc_setting": None,
    }

    coordinator.data.update({"6105": 80, "11009": 2000, "11011": 2100, "11010": 2200})

    assert {key: entity.native_value for key, entity in entities.items()} == {
        "backup_soc": 80,
        "inverter_input_limit": 2000,
        "max_output_power": 2100,
        "feed_in_power_limit": 2200,
        "power_setting": None,
        "soc_setting": None,
    }


@pytest.mark.parametrize(
    ("model", "descriptions", "expected_ids"),
    [
        (
            "BK1600/BK1600Ultra",
            NUMBERS_GEN1,
            {"control-entry_power_setting", "control-entry_soc_setting"},
        ),
        (
            "SolidFlex/PowerFlex2000",
            NUMBERS_GEN2,
            {
                "control-entry_backup_soc",
                "control-entry_inverter_input_limit",
                "control-entry_max_output_power",
                "control-entry_feed_in_power_limit",
                "control-entry_power_setting",
                "control-entry_soc_setting",
            },
        ),
    ],
)
def test_every_number_keeps_its_unique_id(model, descriptions, expected_ids) -> None:
    coordinator = FakeCoordinator(model)

    assert {
        IndevoltNumberEntity(coordinator, description).unique_id
        for description in descriptions
    } == expected_ids


@pytest.mark.parametrize(
    ("model", "descriptions", "key", "value", "point"),
    [
        ("BK1600/BK1600Ultra", NUMBERS_GEN1, "power_setting", 800.0, 47016),
        ("BK1600/BK1600Ultra", NUMBERS_GEN1, "soc_setting", 80.0, 47017),
        ("SolidFlex/PowerFlex2000", NUMBERS_GEN2, "backup_soc", 80.0, 1142),
        (
            "SolidFlex/PowerFlex2000",
            NUMBERS_GEN2,
            "inverter_input_limit",
            1200.0,
            1138,
        ),
        (
            "SolidFlex/PowerFlex2000",
            NUMBERS_GEN2,
            "max_output_power",
            1800.0,
            1147,
        ),
        (
            "SolidFlex/PowerFlex2000",
            NUMBERS_GEN2,
            "feed_in_power_limit",
            900.0,
            1146,
        ),
        (
            "SolidFlex/PowerFlex2000",
            NUMBERS_GEN2,
            "power_setting",
            2400.0,
            47016,
        ),
        (
            "SolidFlex/PowerFlex2000",
            NUMBERS_GEN2,
            "soc_setting",
            80.0,
            47017,
        ),
    ],
)
@pytest.mark.asyncio
async def test_every_number_write_keeps_point_float_and_refresh(
    model,
    descriptions,
    key,
    value,
    point,
) -> None:
    coordinator = FakeCoordinator(model)
    description = next(item for item in descriptions if item.key == key)
    entity = IndevoltNumberEntity(coordinator, description)

    await entity.async_set_native_value(value)

    assert coordinator.api.writes == [(point, [value])]
    assert type(coordinator.api.writes[0][1][0]) is float
    assert coordinator.refreshes == 1


@pytest.mark.parametrize(
    ("model", "descriptions", "key", "value", "point"),
    [
        ("BK1600/BK1600Ultra", NUMBERS_GEN1, "power_setting", 10_801, 47016),
        ("BK1600/BK1600Ultra", NUMBERS_GEN1, "soc_setting", 101, 47017),
        ("SolidFlex/PowerFlex2000", NUMBERS_GEN2, "backup_soc", 101, 1142),
    ],
)
@pytest.mark.asyncio
async def test_direct_number_calls_keep_existing_narrow_validation_scope(
    model,
    descriptions,
    key,
    value,
    point,
) -> None:
    coordinator = FakeCoordinator(model)
    description = next(item for item in descriptions if item.key == key)
    entity = IndevoltNumberEntity(coordinator, description)

    await entity.async_set_native_value(value)

    assert coordinator.api.writes == [(point, [value])]
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_number_false_result_still_refreshes() -> None:
    api = RecordingAPI(result=False)
    coordinator = FakeCoordinator("BK1600/BK1600Ultra", api=api)
    entity = IndevoltNumberEntity(coordinator, NUMBERS_GEN1[1])

    await entity.async_set_native_value(80.0)

    assert api.writes == [(47017, [80.0])]
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_number_exception_stops_before_refresh() -> None:
    api = RecordingAPI(error=RuntimeError("number write failed"))
    coordinator = FakeCoordinator("BK1600/BK1600Ultra", api=api)
    entity = IndevoltNumberEntity(coordinator, NUMBERS_GEN1[1])

    with pytest.raises(RuntimeError, match="^number write failed$"):
        await entity.async_set_native_value(80.0)

    assert api.writes == [(47017, [80.0])]
    assert coordinator.refreshes == 0


@pytest.mark.parametrize(
    ("model", "expected_keys"),
    [
        ("BK1600/BK1600Ultra", ["state_setting"]),
        ("prefix-BK1600-suffix", ["state_setting"]),
        (
            "SolidFlex/PowerFlex2000",
            ["work_mode", "state_setting", "load_setting"],
        ),
        ("FutureModel", ["work_mode", "state_setting", "load_setting"]),
    ],
)
@pytest.mark.asyncio
async def test_select_setup_keeps_exact_route_and_definition_order(
    monkeypatch,
    model,
    expected_keys,
) -> None:
    coordinator = FakeCoordinator(model)
    added = []
    monkeypatch.setattr(
        select_platform,
        "IndevoltSelectEntity",
        lambda coordinator, description: description.key,
    )

    await select_platform.async_setup_entry(
        None,
        _entry(coordinator),
        lambda entities: added.extend(entities),
    )

    assert added == expected_keys


@pytest.mark.parametrize(
    ("descriptions", "key", "raw_value", "expected"),
    [
        (SELECTS_GEN1, "state_setting", 1000, "Standby"),
        (SELECTS_GEN1, "state_setting", 1001, "Charging"),
        (SELECTS_GEN1, "state_setting", 1002, "Discharging"),
        (SELECTS_GEN1, "state_setting", 999, None),
        (SELECTS_GEN2, "work_mode", 1, "Self-Consumed Prioritized"),
        (SELECTS_GEN2, "work_mode", 4, "Real-Time Control"),
        (SELECTS_GEN2, "work_mode", 5, "Charge/Discharge Schedule"),
        (SELECTS_GEN2, "work_mode", 0, None),
        (SELECTS_GEN2, "work_mode", None, None),
        (SELECTS_GEN2, "state_setting", 1000, "Standby"),
        (SELECTS_GEN2, "state_setting", 1001, "Charging"),
        (SELECTS_GEN2, "state_setting", 1002, "Discharging"),
        (SELECTS_GEN2, "state_setting", None, None),
        (SELECTS_GEN2, "load_setting", 1, None),
    ],
)
def test_select_current_option_keeps_every_read_mapping(
    descriptions,
    key,
    raw_value,
    expected,
) -> None:
    model = "BK1600/BK1600Ultra" if descriptions is SELECTS_GEN1 else "FutureModel"
    description = next(item for item in descriptions if item.key == key)
    data = {description.read_point: raw_value} if description.read_point else {}
    coordinator = FakeCoordinator(model, data)
    entity = IndevoltSelectEntity(coordinator, description)

    assert entity.current_option == expected


@pytest.mark.parametrize("data", [{}, {"6001": None}])
def test_bk_select_preserves_missing_state_type_error(data) -> None:
    coordinator = FakeCoordinator("BK1600/BK1600Ultra", data)
    entity = IndevoltSelectEntity(coordinator, SELECTS_GEN1[0])

    with pytest.raises(TypeError):
        _ = entity.current_option


@pytest.mark.parametrize(
    ("descriptions", "key", "option", "point", "value"),
    [
        (SELECTS_GEN1, "state_setting", "Standby", 47015, 0),
        (SELECTS_GEN1, "state_setting", "Charging", 47015, 1),
        (SELECTS_GEN1, "state_setting", "Discharging", 47015, 2),
        (SELECTS_GEN2, "work_mode", "Self-Consumed Prioritized", 47005, 1),
        (SELECTS_GEN2, "work_mode", "Real-Time Control", 47005, 4),
        (SELECTS_GEN2, "work_mode", "Charge/Discharge Schedule", 47005, 5),
        (SELECTS_GEN2, "state_setting", "Standby", 47015, 0),
        (SELECTS_GEN2, "state_setting", "Charging", 47015, 1),
        (SELECTS_GEN2, "state_setting", "Discharging", 47015, 2),
        (SELECTS_GEN2, "load_setting", "Smart Plug", 1, 1),
        (SELECTS_GEN2, "load_setting", "Meter", 1, 2),
        (SELECTS_GEN2, "load_setting", "Key Load", 1, 3),
        (SELECTS_GEN2, "load_setting", "Custom", 1, 4),
    ],
)
@pytest.mark.asyncio
async def test_every_select_option_keeps_write_and_refresh_contract(
    descriptions,
    key,
    option,
    point,
    value,
) -> None:
    model = "BK1600/BK1600Ultra" if descriptions is SELECTS_GEN1 else "FutureModel"
    coordinator = FakeCoordinator(model)
    description = next(item for item in descriptions if item.key == key)
    entity = IndevoltSelectEntity(coordinator, description)

    await entity.async_select_option(option)

    assert entity._attr_current_option == option
    assert coordinator.api.writes == [(point, [value])]
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_select_false_result_still_refreshes() -> None:
    api = RecordingAPI(result=False)
    coordinator = FakeCoordinator("FutureModel", api=api)
    entity = IndevoltSelectEntity(coordinator, SELECTS_GEN2[0])

    await entity.async_select_option("Real-Time Control")

    assert api.writes == [(47005, [4])]
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_select_exception_keeps_optimistic_option_and_skips_refresh() -> None:
    api = RecordingAPI(error=RuntimeError("select write failed"))
    coordinator = FakeCoordinator("FutureModel", api=api)
    entity = IndevoltSelectEntity(coordinator, SELECTS_GEN2[0])

    with pytest.raises(RuntimeError, match="^select write failed$"):
        await entity.async_select_option("Real-Time Control")

    assert entity._attr_current_option == "Real-Time Control"
    assert api.writes == [(47005, [4])]
    assert coordinator.refreshes == 0


@pytest.mark.asyncio
async def test_select_unknown_option_has_no_side_effect() -> None:
    coordinator = FakeCoordinator("FutureModel", {"7101": 1})
    entity = IndevoltSelectEntity(coordinator, SELECTS_GEN2[0])

    await entity.async_select_option("Unknown")

    assert entity._attr_current_option is None
    assert coordinator.api.writes == []
    assert coordinator.refreshes == 0
    assert entity.current_option == "Self-Consumed Prioritized"


@pytest.mark.parametrize(
    ("model", "data", "expected_keys"),
    [
        ("BK1600/BK1600Ultra", {"7171": 1, "2618": 1001, "680": 1}, []),
        ("prefix-BK1600-suffix", {"7171": 1}, []),
        ("FutureModel", {}, []),
        ("FutureModel", {"7171": None}, ["light"]),
        ("FutureModel", {"2618": 0, "680": False}, ["grid", "bypass"]),
        (
            "SolidFlex/PowerFlex2000",
            {"7171": 0, "2618": 1001, "680": 1},
            ["light", "grid", "bypass"],
        ),
    ],
)
@pytest.mark.asyncio
async def test_switch_setup_keeps_model_and_key_presence_contract(
    monkeypatch,
    model,
    data,
    expected_keys,
) -> None:
    coordinator = FakeCoordinator(model, data)
    added = []
    monkeypatch.setattr(
        switch_platform,
        "IndevoltSwitchEntity",
        lambda coordinator, description: description.key,
    )

    await switch_platform.async_setup_entry(
        None,
        _entry(coordinator),
        lambda entities: added.extend(entities),
    )

    assert added == expected_keys


@pytest.mark.parametrize(
    ("key", "read_point", "write_point", "initial", "on_after_optimistic"),
    [
        ("light", "7171", 7265, 0, True),
        ("grid", "2618", 1143, 1000, False),
        ("bypass", "680", 7266, 0, True),
    ],
)
@pytest.mark.asyncio
async def test_every_switch_keeps_optimistic_and_write_contract(
    monkeypatch,
    key,
    read_point,
    write_point,
    initial,
    on_after_optimistic,
) -> None:
    coordinator = FakeCoordinator("FutureModel", {read_point: initial, "other": 7})
    description = next(item for item in SWITCHES if item.key == key)
    entity = IndevoltSwitchEntity(coordinator, description)
    written_states = []
    monkeypatch.setattr(
        entity,
        "async_write_ha_state",
        lambda: written_states.append(entity.is_on),
    )

    await entity.async_turn_on()
    await entity.async_turn_off()

    assert coordinator.updated_data == [
        {read_point: True, "other": 7},
        {read_point: False, "other": 7},
    ]
    assert written_states == [on_after_optimistic, False]
    assert coordinator.api.writes == [(write_point, [1]), (write_point, [0])]
    assert coordinator.refreshes == 0


def test_switch_availability_combines_coordinator_and_point_state() -> None:
    description = next(item for item in SWITCHES if item.key == "light")
    coordinator = FakeCoordinator("FutureModel", {"7171": 1})
    entity = IndevoltSwitchEntity(coordinator, description)

    assert entity.available is True

    coordinator.last_update_success = False
    assert entity.available is False

    coordinator.last_update_success = True
    coordinator.data["7171"] = None
    assert entity.available is False


@pytest.mark.asyncio
async def test_switch_false_result_keeps_optimistic_state_without_refresh(
    monkeypatch,
) -> None:
    api = RecordingAPI(result=False)
    coordinator = FakeCoordinator("FutureModel", {"7171": 0}, api=api)
    entity = IndevoltSwitchEntity(coordinator, SWITCHES[0])
    monkeypatch.setattr(entity, "async_write_ha_state", lambda: None)

    await entity.async_turn_on()

    assert coordinator.data == {"7171": True}
    assert api.writes == [(7265, [1])]
    assert coordinator.refreshes == 0


@pytest.mark.asyncio
async def test_switch_exception_leaves_optimistic_state_without_refresh(
    monkeypatch,
) -> None:
    api = RecordingAPI(error=RuntimeError("switch write failed"))
    coordinator = FakeCoordinator("FutureModel", {"680": 0}, api=api)
    description = next(item for item in SWITCHES if item.key == "bypass")
    entity = IndevoltSwitchEntity(coordinator, description)
    monkeypatch.setattr(entity, "async_write_ha_state", lambda: None)

    with pytest.raises(RuntimeError, match="^switch write failed$"):
        await entity.async_turn_on()

    assert coordinator.data == {"680": True}
    assert api.writes == [(7266, [1])]
    assert coordinator.refreshes == 0


@pytest.mark.asyncio
async def test_switch_state_write_exception_prevents_device_write(monkeypatch) -> None:
    coordinator = FakeCoordinator("FutureModel", {"7171": 0})
    entity = IndevoltSwitchEntity(coordinator, SWITCHES[0])

    def fail_state_write() -> None:
        raise RuntimeError("state write failed")

    monkeypatch.setattr(entity, "async_write_ha_state", fail_state_write)

    with pytest.raises(RuntimeError, match="^state write failed$"):
        await entity.async_turn_on()

    assert coordinator.data == {"7171": True}
    assert coordinator.api.writes == []
    assert coordinator.refreshes == 0


def test_every_select_and_switch_keeps_its_unique_id() -> None:
    bk = FakeCoordinator("BK1600/BK1600Ultra")
    default = FakeCoordinator("FutureModel")

    assert {
        IndevoltSelectEntity(bk, description).unique_id for description in SELECTS_GEN1
    } == {"control-entry_state_setting"}
    assert {
        IndevoltSelectEntity(default, description).unique_id
        for description in SELECTS_GEN2
    } == {
        "control-entry_work_mode",
        "control-entry_state_setting",
        "control-entry_load_setting",
        "control-entry_led_light_strip_mode",
    }
    assert {
        IndevoltSwitchEntity(default, description).unique_id for description in SWITCHES
    } == {
        "control-entry_light",
        "control-entry_grid",
        "control-entry_bypass",
    }
