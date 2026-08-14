"""Self-check the independent OpenData new-point evidence."""

from tests.models._opendata_point_additions import (
    ADDITIONAL_DEFAULT_POINT_BATCHES,
    ADDITIONAL_DEFAULT_READ_POINTS,
    BASELINE_DEFAULT_POINT_BATCHES,
    CONTROL_STATE_POINT_BATCHES,
    CONTROL_STATE_READ_POINTS,
    DEFAULT_CAPABILITY_POINT_BATCHES,
    DEFAULT_CAPABILITY_READ_POINTS,
    flattened,
)


def test_additional_read_point_evidence_is_complete_and_unambiguous() -> None:
    """The protocol diff contains 136 unique points in 17 eight-point batches."""
    assert len(ADDITIONAL_DEFAULT_READ_POINTS) == 136
    assert len(set(ADDITIONAL_DEFAULT_READ_POINTS)) == 136
    assert len(ADDITIONAL_DEFAULT_POINT_BATCHES) == 17
    assert all(len(batch) == 8 for batch in ADDITIONAL_DEFAULT_POINT_BATCHES)
    assert flattened(ADDITIONAL_DEFAULT_POINT_BATCHES) == ADDITIONAL_DEFAULT_READ_POINTS


def test_additional_read_points_do_not_relabel_baseline_points() -> None:
    """No point from the preserved 98-point baseline is called a documented addition."""
    assert set(flattened(BASELINE_DEFAULT_POINT_BATCHES)).isdisjoint(
        ADDITIONAL_DEFAULT_READ_POINTS
    )


def test_new_bidirectional_controls_add_only_their_three_needed_state_reads() -> None:
    """A user control should report the device value without importing old gaps."""
    assert CONTROL_STATE_READ_POINTS == (8646, 8647, 2802)
    assert CONTROL_STATE_POINT_BATCHES == ((8646, 8647, 2802),)
    assert DEFAULT_CAPABILITY_READ_POINTS == (
        ADDITIONAL_DEFAULT_READ_POINTS + (8646, 8647, 2802)
    )
    assert DEFAULT_CAPABILITY_POINT_BATCHES == (
        ADDITIONAL_DEFAULT_POINT_BATCHES + ((8646, 8647, 2802),)
    )
    assert set(CONTROL_STATE_READ_POINTS).isdisjoint(ADDITIONAL_DEFAULT_READ_POINTS)
