"""Completeness checks for the guessed OpenData user capabilities."""

from tests.models._opendata_point_additions import (
    ADDITIONAL_DEFAULT_READ_POINTS,
    ADDITIONAL_DEFAULT_SET_POINTS,
    BASELINE_DEFAULT_POINT_BATCHES,
    CONTROL_STATE_READ_POINTS,
    flattened,
)
from tests.models.opendata_capabilities import (
    CONTROL_CAPABILITY_MARKER_POINT,
    GET_USER_CAPABILITIES,
    SET_USER_CAPABILITIES,
)


def test_every_additional_read_point_has_one_user_capability_guess() -> None:
    """No documented read addition may disappear between protocol and HA design."""
    mapped_points = tuple(capability.point for capability in GET_USER_CAPABILITIES)

    assert len(mapped_points) == 136
    assert len(set(mapped_points)) == len(mapped_points)
    assert mapped_points == ADDITIONAL_DEFAULT_READ_POINTS


def test_every_additional_write_point_has_one_exposure_decision() -> None:
    """Every documented write addition must be exposed or deliberately hidden."""
    mapped_points = tuple(capability.point for capability in SET_USER_CAPABILITIES)

    assert len(mapped_points) == 63
    assert len(set(mapped_points)) == len(mapped_points)
    assert mapped_points == ADDITIONAL_DEFAULT_SET_POINTS


def test_write_capabilities_have_one_reviewable_firmware_gate() -> None:
    """Old firmware must not gain guessed controls solely from old read points."""
    assert CONTROL_CAPABILITY_MARKER_POINT == 1127
    assert CONTROL_CAPABILITY_MARKER_POINT in ADDITIONAL_DEFAULT_READ_POINTS


def test_non_user_writes_are_limited_to_transport_and_data_injection() -> None:
    """Protocol inputs must not accidentally become misleading HA controls."""
    hidden_by_exposure = {
        exposure: {
            capability.point
            for capability in SET_USER_CAPABILITIES
            if capability.exposure == exposure
        }
        for exposure in {"existing_control_transport", "external_data_injection"}
    }

    assert hidden_by_exposure == {
        "existing_control_transport": {11009, 2618, 6505, 11010},
        "external_data_injection": {15203, 15204, 18000, 18001},
    }
    assert all(
        capability.key is None
        and capability.user_value is None
        and capability.wire_value is None
        for capability in SET_USER_CAPABILITIES
        if not capability.user_visible
    )


def test_all_other_writes_are_reachable_as_user_controls() -> None:
    visible = [
        capability for capability in SET_USER_CAPABILITIES if capability.user_visible
    ]

    assert len(visible) == 55
    assert {capability.entity_domain for capability in visible} == {
        "number",
        "select",
        "time",
    }
    assert all(capability.key is not None for capability in visible)
    assert all(capability.user_value is not None for capability in visible)
    assert all(capability.wire_value is not None for capability in visible)
    assert all(capability.read_point is not None for capability in visible)
    assert all(capability.expected_initial_state is not None for capability in visible)


def test_simulated_load_read_and_write_slots_are_paired_one_to_one() -> None:
    load_reads = {
        capability.key: capability.point
        for capability in GET_USER_CAPABILITIES
        if capability.key.startswith("simulated_load_slot_")
    }
    load_writes = {
        capability.key: (capability.point, capability.read_point)
        for capability in SET_USER_CAPABILITIES
        if capability.key is not None
        and capability.key.startswith("simulated_load_slot_")
    }

    assert load_reads == {
        f"simulated_load_slot_{slot + 1:02d}": 26000 + slot for slot in range(48)
    }
    assert load_writes == {
        f"simulated_load_slot_{slot + 1:02d}": (12197 + slot, 26000 + slot)
        for slot in range(48)
    }


def test_control_state_comes_from_documented_or_baseline_read_points() -> None:
    read_points = {
        capability.read_point
        for capability in SET_USER_CAPABILITIES
        if capability.user_visible
    }
    already_polled = set(flattened(BASELINE_DEFAULT_POINT_BATCHES))

    assert read_points - set(ADDITIONAL_DEFAULT_READ_POINTS) - already_polled == set(
        CONTROL_STATE_READ_POINTS
    )


def test_default_disabled_guesses_are_only_high_volume_or_diagnostic_entities() -> None:
    disabled_reads = {
        capability.point
        for capability in GET_USER_CAPABILITIES
        if not capability.enabled_by_default
    }
    disabled_writes = {
        capability.point
        for capability in SET_USER_CAPABILITIES
        if capability.user_visible and not capability.enabled_by_default
    }

    assert disabled_reads == {9267, *range(26000, 26048)}
    assert disabled_writes == set(range(12197, 12245))


def test_every_guessed_number_control_has_a_reviewable_user_range() -> None:
    numbers = [
        capability
        for capability in SET_USER_CAPABILITIES
        if capability.exposure == "number"
    ]

    assert len(numbers) == 50
    assert all(capability.minimum is not None for capability in numbers)
    assert all(capability.maximum is not None for capability in numbers)
    assert all(capability.step == 1 for capability in numbers)
    assert all(capability.unit is not None for capability in numbers)
    assert all(type(capability.user_value) is float for capability in numbers)
    assert all(type(capability.wire_value) is float for capability in numbers)


def test_every_guessed_select_control_has_reviewable_options() -> None:
    selects = [
        capability
        for capability in SET_USER_CAPABILITIES
        if capability.entity_domain == "select"
    ]

    assert len(selects) == 2
    assert all(capability.options for capability in selects)
    assert all(capability.user_value in capability.options for capability in selects)


def test_guessed_entity_unique_ids_do_not_collide() -> None:
    read_unique_ids = [
        capability.unique_id("CAPABILITY-SN") for capability in GET_USER_CAPABILITIES
    ]
    visible_write_unique_ids = [
        f"CAPABILITY-SN_{capability.key}"
        for capability in SET_USER_CAPABILITIES
        if capability.user_visible
    ]

    assert len(set(read_unique_ids)) == len(read_unique_ids)
    # Read/write sides of a bidirectional control intentionally share one entity.
    assert set(read_unique_ids) & set(visible_write_unique_ids) == {
        "CAPABILITY-SN_deep_sleep_start_time",
        "CAPABILITY-SN_deep_sleep_end_time",
        *(f"CAPABILITY-SN_simulated_load_slot_{slot + 1:02d}" for slot in range(48)),
    }
