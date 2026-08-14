"""BK1600 Ultra isolation from the SF/PF documented capability guesses."""

from __future__ import annotations

import pytest

from tests.models._opendata_user_testing import SERIAL, ModelUserHarness
from tests.models.opendata_capabilities import (
    GET_USER_CAPABILITIES,
    SET_USER_CAPABILITIES,
)

MODEL = "BK1600/BK1600Ultra"


@pytest.mark.asyncio
async def test_bk1600_ultra_never_exposes_default_route_capability_capabilities() -> (
    None
):
    harness = ModelUserHarness(MODEL)
    await harness.set_up_platforms()
    registered_unique_ids = {unique_id for _, unique_id in harness.entities}
    default_route_capability_unique_ids = {
        capability.unique_id(SERIAL) for capability in GET_USER_CAPABILITIES
    } | {
        f"{SERIAL}_{capability.key}"
        for capability in SET_USER_CAPABILITIES
        if capability.user_visible
    }

    assert registered_unique_ids.isdisjoint(default_route_capability_unique_ids)
