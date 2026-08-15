"""PowerFlex2000 user-facing acceptance tests for every documented point addition."""

from __future__ import annotations

import pytest

from tests.models._opendata_point_additions import DEFAULT_NON_USER_READ_POINTS
from tests.models._opendata_user_testing import (
    assert_get_point_is_not_exposed_as_an_entity,
    assert_get_user_capability,
    assert_get_user_capability_missing_value_behavior,
    assert_set_point_is_not_exposed_as_a_new_user_control,
    assert_set_user_capability,
    assert_set_user_capability_missing_value_behavior,
)
from tests.models.opendata_capabilities import (
    GET_USER_CAPABILITIES,
    SET_USER_CAPABILITIES,
    GetUserCapability,
    SetUserCapability,
)

MODEL = "PowerFlex2000"
VISIBLE_SET_CAPABILITIES = tuple(
    capability for capability in SET_USER_CAPABILITIES if capability.user_visible
)
NON_USER_SET_CAPABILITIES = tuple(
    capability for capability in SET_USER_CAPABILITIES if not capability.user_visible
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    GET_USER_CAPABILITIES,
    ids=lambda capability: f"get-{capability.point}-{capability.domain}",
)
async def test_powerflex2000_exposes_each_new_value_to_the_user(
    capability: GetUserCapability,
) -> None:
    await assert_get_user_capability(MODEL, capability)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    GET_USER_CAPABILITIES,
    ids=lambda capability: f"missing-{capability.point}-{capability.domain}",
)
async def test_powerflex2000_handles_each_new_value_disappearing(
    capability: GetUserCapability,
) -> None:
    await assert_get_user_capability_missing_value_behavior(MODEL, capability)


@pytest.mark.asyncio
@pytest.mark.parametrize("point", DEFAULT_NON_USER_READ_POINTS)
async def test_powerflex2000_does_not_duplicate_non_user_read_points(
    point: int,
) -> None:
    await assert_get_point_is_not_exposed_as_an_entity(MODEL, point)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    VISIBLE_SET_CAPABILITIES,
    ids=lambda capability: f"set-{capability.point}-{capability.entity_domain}",
)
async def test_powerflex2000_operates_each_new_user_control(
    capability: SetUserCapability,
) -> None:
    await assert_set_user_capability(MODEL, capability)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    VISIBLE_SET_CAPABILITIES,
    ids=lambda capability: f"missing-{capability.point}-{capability.entity_domain}",
)
async def test_powerflex2000_handles_each_new_control_readback_disappearing(
    capability: SetUserCapability,
) -> None:
    await assert_set_user_capability_missing_value_behavior(MODEL, capability)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    NON_USER_SET_CAPABILITIES,
    ids=lambda capability: f"set-{capability.point}-not-user-control",
)
async def test_powerflex2000_keeps_each_non_user_write_point_out_of_ha_controls(
    capability: SetUserCapability,
) -> None:
    await assert_set_point_is_not_exposed_as_a_new_user_control(MODEL, capability)
