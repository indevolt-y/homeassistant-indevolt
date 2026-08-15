"""BK1600 Ultra isolation from the SF/PF documented capability guesses."""

from __future__ import annotations

import pytest

from tests.models._opendata_point_additions import BK_NON_USER_READ_POINTS
from tests.models._opendata_user_testing import (
    SERIAL,
    ModelUserHarness,
    assert_get_point_is_not_exposed_as_an_entity,
    assert_get_user_capability,
    assert_get_user_capability_missing_value_behavior,
)
from tests.models.opendata_capabilities import (
    BK_GET_USER_CAPABILITIES,
    GET_USER_CAPABILITIES,
    SET_USER_CAPABILITIES,
    GetUserCapability,
)

MODEL = "BK1600/BK1600Ultra"
BK_EXISTING_READ_POINTS = {
    1501,
    1502,
    1505,
    1664,
    1665,
    2101,
    2107,
    2108,
    6000,
    6001,
    6002,
    6004,
    6005,
    6006,
    6007,
    6105,
    7101,
    7120,
    21028,
}


@pytest.mark.asyncio
async def test_bk1600_ultra_never_exposes_default_route_capability_capabilities() -> (
    None
):
    harness = ModelUserHarness(MODEL)
    await harness.set_up_platforms()
    registered_unique_ids = {unique_id for _, unique_id in harness.entities}
    default_route_capability_unique_ids = {
        capability.unique_id(SERIAL)
        for capability in GET_USER_CAPABILITIES
        if capability.point not in BK_EXISTING_READ_POINTS
        and capability.point not in {item.point for item in BK_GET_USER_CAPABILITIES}
    } | {
        f"{SERIAL}_{capability.key}"
        for capability in SET_USER_CAPABILITIES
        if capability.user_visible
    }

    assert registered_unique_ids.isdisjoint(default_route_capability_unique_ids)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    BK_GET_USER_CAPABILITIES,
    ids=lambda capability: f"get-{capability.point}-{capability.domain}",
)
async def test_bk1600_ultra_exposes_each_bk_value_to_the_user(
    capability: GetUserCapability,
) -> None:
    await assert_get_user_capability(MODEL, capability)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    BK_GET_USER_CAPABILITIES,
    ids=lambda capability: f"missing-{capability.point}-{capability.domain}",
)
async def test_bk1600_ultra_handles_each_new_value_disappearing(
    capability: GetUserCapability,
) -> None:
    await assert_get_user_capability_missing_value_behavior(MODEL, capability)


@pytest.mark.asyncio
@pytest.mark.parametrize("point", BK_NON_USER_READ_POINTS)
async def test_bk1600_ultra_keeps_non_user_read_points_out_of_ha(point: int) -> None:
    await assert_get_point_is_not_exposed_as_an_entity(MODEL, point)
