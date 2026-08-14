"""Independent acceptance data for the OpenData read-point expansion.

The read-point tuple is the ordered SF2000/PF2000 ``Indevolt.GetData`` diff
between INDEVOLT/indevolt-doc commits d99743d59f5f and e9940468c09a.  The
later commit includes the correction that moved 75 writable points out of
``GetData``. Keep this test-side evidence independent from production point
constants so a production omission cannot make its own test pass.

The SetData cases use the same corrected document and exclude the 12 write
points already present in the integration baseline.
"""

from __future__ import annotations

from dataclasses import dataclass

BASELINE_DEFAULT_POINT_BATCHES: tuple[tuple[int, ...], ...] = (
    (142, 606, 667, 680, 1118, 1109, 1119, 1120),
    (1136, 1137, 1138, 1139, 1140, 1141, 1142, 1143),
    (1098, 1099, 1501, 1502, 1600, 1601, 1602, 1603),
    (1632, 1633, 1634, 1635, 1664, 1665, 1666, 1667),
    (2101, 2104, 2105, 2107, 2108, 2600, 2612, 2618),
    (6000, 6001, 6002, 6004, 6005, 6006, 6007, 6105),
    (7101, 7120, 7171, 9000, 9004, 9008, 9009, 9011),
    (9012, 9013, 9016, 9020, 9021, 9023, 9030, 9032),
    (9035, 9039, 9040, 9042, 9049, 9051, 9054, 9058),
    (9059, 9061, 9068, 9070, 9149, 9153, 9154, 9156),
    (9163, 9165, 9202, 9206, 9216, 9218, 9219, 9222),
    (11009, 11010, 11011, 11016, 11034, 19173, 19174, 19175),
    (19176, 19177),
)

ADDITIONAL_DEFAULT_READ_POINTS: tuple[int, ...] = (
    2278,
    11032,
    6010,
    114,
    115,
    11019,
    11020,
    9003,
    9019,
    9038,
    9057,
    9152,
    9205,
    9002,
    9018,
    9028,
    9037,
    9047,
    9056,
    9066,
    9151,
    9161,
    9081,
    9082,
    9097,
    9098,
    9113,
    9114,
    9129,
    9130,
    9145,
    9146,
    9204,
    9214,
    9267,
    9280,
    9281,
    9405,
    9079,
    9080,
    9095,
    9096,
    9111,
    9112,
    9127,
    9128,
    9143,
    9144,
    9278,
    9279,
    64100,
    669,
    4,
    614,
    11028,
    11029,
    11030,
    2086,
    2083,
    2095,
    2098,
    2097,
    2099,
    2275,
    8100,
    11007,
    11036,
    5000,
    120,
    11031,
    8500,
    7119,
    7124,
    7126,
    7127,
    8138,
    8102,
    8132,
    8133,
    1127,
    11006,
    11008,
    632,
    35001,
    35002,
    6107,
    6109,
    6108,
    26000,
    26001,
    26002,
    26003,
    26004,
    26005,
    26006,
    26007,
    26008,
    26009,
    26010,
    26011,
    26012,
    26013,
    26014,
    26015,
    26016,
    26017,
    26018,
    26019,
    26020,
    26021,
    26022,
    26023,
    26024,
    26025,
    26026,
    26027,
    26028,
    26029,
    26030,
    26031,
    26032,
    26033,
    26034,
    26035,
    26036,
    26037,
    26038,
    26039,
    26040,
    26041,
    26042,
    26043,
    26044,
    26045,
    26046,
    26047,
)

ADDITIONAL_DEFAULT_POINT_BATCHES: tuple[tuple[int, ...], ...] = tuple(
    ADDITIONAL_DEFAULT_READ_POINTS[index : index + 8]
    for index in range(0, len(ADDITIONAL_DEFAULT_READ_POINTS), 8)
)

# These three reads predate the point-table additions, but their matching SetData
# points become user controls in this design. Poll them so those controls show the
# device's real value instead of an invented optimistic value.
CONTROL_STATE_READ_POINTS: tuple[int, ...] = (8646, 8647, 2802)
CONTROL_STATE_POINT_BATCHES: tuple[tuple[int, ...], ...] = (CONTROL_STATE_READ_POINTS,)
DEFAULT_CAPABILITY_READ_POINTS = (
    ADDITIONAL_DEFAULT_READ_POINTS + CONTROL_STATE_READ_POINTS
)
DEFAULT_CAPABILITY_POINT_BATCHES = (
    ADDITIONAL_DEFAULT_POINT_BATCHES + CONTROL_STATE_POINT_BATCHES
)

# Documented GetData points that are outside both the current polling baseline
# and the user-capability definitions above.  Keep them explicit so every point
# has an executable expectation even before production support exists.
REMAINING_DEFAULT_READ_POINTS: tuple[int, ...] = (
    9284,
    9285,
    11035,
    11039,
    11037,
    0,
    1505,
)

REMAINING_BK_READ_POINTS: tuple[int, ...] = (
    0,
    1118,
    1107,
    1119,
    311,
    142,
    2618,
    2617,
    4,
    2619,
    680,
    7170,
    667,
    7620,
    10112,
    10113,
    10114,
    10115,
    10116,
    10117,
    10118,
    10119,
    10120,
    10121,
    10122,
    1632,
    1600,
    1633,
    1601,
)


def flattened(batches: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
    """Flatten immutable expected request batches."""
    return tuple(point for batch in batches for point in batch)


BASELINE_DEFAULT_SET_POINTS: tuple[int, ...] = (
    47005,
    47015,
    47016,
    47017,
    1147,
    1146,
    1143,
    1138,
    1,
    7266,
    1142,
    7265,
)


@dataclass(frozen=True, slots=True)
class SetPointCase:
    """One documented write point with a representative transport scalar."""

    point: int
    transport_value: int
    description: str


ADDITIONAL_DEFAULT_SET_CASES: tuple[SetPointCase, ...] = (
    SetPointCase(11009, 100, "AC charging power limit"),
    SetPointCase(2618, 1, "grid charging enable"),
    SetPointCase(6505, 50, "backup SOC"),
    SetPointCase(11010, 0, "grid feed-in power limit"),
    SetPointCase(15203, 0, "meter phase U power"),
    SetPointCase(15204, 0, "meter phase U power"),
    SetPointCase(18000, 1, "smart socket connection state"),
    SetPointCase(18001, 0, "smart socket power"),
    SetPointCase(35001, 0x121E, "deep-sleep start time"),
    SetPointCase(35002, 0x061E, "deep-sleep stop time"),
    SetPointCase(35005, 1, "LED light-strip mode"),
    SetPointCase(8646, 30, "forced full-charge interval"),
    SetPointCase(8647, 0x0800, "forced full-charge start time"),
    SetPointCase(2802, 100, "forced AC charging power"),
    SetPointCase(4, 4, "system operating mode"),
    *(
        SetPointCase(12197 + slot, 0, f"simulated load time slot {slot + 1}")
        for slot in range(48)
    ),
)

ADDITIONAL_DEFAULT_SET_POINTS: tuple[int, ...] = tuple(
    case.point for case in ADDITIONAL_DEFAULT_SET_CASES
)
