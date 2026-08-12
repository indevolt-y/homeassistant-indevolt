"""End-to-end equivalence tests for Home Assistant Number writes."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.components.number import async_set_value as async_ha_set_value
from homeassistant.exceptions import ServiceValidationError

from custom_components.indevolt.number import NUMBERS_GEN2, IndevoltNumberEntity


class RecordingAPI:
    """Record Number writes and optionally return or raise a configured result."""

    def __init__(self, *, result: bool = True, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.writes: list[tuple[int, list[float]]] = []

    async def set_data(self, *, point: int, value: list[float]) -> bool:
        self.writes.append((point, value))
        if self.error is not None:
            raise self.error
        return self.result


class FakeCoordinator:
    """Provide the exact state used by the Number write path."""

    def __init__(self, api: RecordingAPI) -> None:
        self.api = api
        self.config_entry = SimpleNamespace(
            unique_id="number-equivalence-entry",
            data={"device_model": "SolidFlex/PowerFlex2000"},
        )
        self.data = {}
        self.refreshes = 0

    async def async_refresh(self) -> None:
        self.refreshes += 1


def make_entity(
    key: str, api: RecordingAPI
) -> tuple[IndevoltNumberEntity, FakeCoordinator]:
    """Build a Number entity without registering it in Home Assistant."""
    coordinator = FakeCoordinator(api)
    description = next(item for item in NUMBERS_GEN2 if item.key == key)
    entity = object.__new__(IndevoltNumberEntity)
    entity.coordinator = coordinator
    entity.entity_description = description
    entity.entity_id = f"number.indevolt_{key}"
    entity.platform_data = SimpleNamespace(
        domain="number",
        platform_name="indevolt",
        default_language_platform_translations={},
    )
    return entity, coordinator


@pytest.mark.parametrize(
    ("key", "value", "point"),
    [
        ("backup_soc", 80.0, 1142),
        ("inverter_input_limit", 2400.0, 1138),
        ("max_output_power", 2400.0, 1147),
        ("feed_in_power_limit", 800.0, 1146),
        ("power_setting", 1200.0, 47016),
        ("soc_setting", 80.0, 47017),
    ],
)
@pytest.mark.asyncio
async def test_ha_number_service_preserves_all_six_float_writes(
    key: str,
    value: float,
    point: int,
) -> None:
    api = RecordingAPI()
    entity, coordinator = make_entity(key, api)

    await async_ha_set_value(entity, SimpleNamespace(data={"value": value}))

    assert api.writes == [(point, [value])]
    assert type(api.writes[0][1][0]) is float
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_false_api_result_keeps_the_existing_refresh_behavior() -> None:
    api = RecordingAPI(result=False)
    entity, coordinator = make_entity("power_setting", api)

    await async_ha_set_value(entity, SimpleNamespace(data={"value": 1200.0}))

    assert api.writes == [(47016, [1200.0])]
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_api_exception_keeps_the_existing_no_refresh_behavior() -> None:
    api = RecordingAPI(error=RuntimeError("write failure"))
    entity, coordinator = make_entity("power_setting", api)

    with pytest.raises(RuntimeError, match="^write failure$"):
        await async_ha_set_value(entity, SimpleNamespace(data={"value": 1200.0}))

    assert api.writes == [(47016, [1200.0])]
    assert coordinator.refreshes == 0


@pytest.mark.asyncio
async def test_ha_service_still_rejects_out_of_range_before_the_api() -> None:
    api = RecordingAPI()
    entity, coordinator = make_entity("power_setting", api)

    with pytest.raises(ServiceValidationError):
        await async_ha_set_value(entity, SimpleNamespace(data={"value": 10801.0}))

    assert api.writes == []
    assert coordinator.refreshes == 0
