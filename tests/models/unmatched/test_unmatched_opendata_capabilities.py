"""Legacy non-BK fallback acceptance for every documented point addition."""

from __future__ import annotations

import pytest

from tests.models._opendata_user_testing import (
    assert_get_user_capability,
    assert_set_user_capability,
)
from tests.models.opendata_capabilities import (
    GET_USER_CAPABILITIES,
    SET_USER_CAPABILITIES,
    GetUserCapability,
    SetUserCapability,
)

MODEL = "FutureModel"
VISIBLE_SET_CAPABILITIES = tuple(
    capability for capability in SET_USER_CAPABILITIES if capability.user_visible
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    GET_USER_CAPABILITIES,
    ids=lambda capability: f"get-{capability.point}-{capability.domain}",
)
async def test_unmatched_model_keeps_default_route_for_each_new_value(
    capability: GetUserCapability,
) -> None:
    await assert_get_user_capability(MODEL, capability)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "capability",
    VISIBLE_SET_CAPABILITIES,
    ids=lambda capability: f"set-{capability.point}-{capability.entity_domain}",
)
async def test_unmatched_model_keeps_default_route_for_each_new_control(
    capability: SetUserCapability,
) -> None:
    await assert_set_user_capability(MODEL, capability)
