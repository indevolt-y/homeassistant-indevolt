"""Additional documented GetData point groups.

The historical polling baselines remain unchanged. These groups are requested
after those baselines so existing point order and eight-point batch boundaries
stay intact.
"""

from __future__ import annotations

SIMULATED_LOAD_READ_POINTS: tuple[int, ...] = tuple(range(26000, 26048))

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
    9405,
    9079,
    9080,
    9095,
    9096,
    9111,
    9112,
    9127,
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
    *SIMULATED_LOAD_READ_POINTS,
)

CONTROL_STATE_READ_POINTS: tuple[int, ...] = (8646, 8647, 2802)
CONTROL_STATE_POINT_BATCHES: tuple[tuple[int, ...], ...] = (CONTROL_STATE_READ_POINTS,)
DEFAULT_CAPABILITY_READ_POINTS = (
    ADDITIONAL_DEFAULT_READ_POINTS + CONTROL_STATE_READ_POINTS
)

REMAINING_DEFAULT_USER_READ_POINTS: tuple[int, ...] = (
    9284,
    9285,
    11039,
    11037,
    1505,
)

REMAINING_BK_USER_READ_POINTS: tuple[int, ...] = (
    1118,
    1107,
    311,
    142,
    2618,
    2617,
    4,
    2619,
    680,
    7170,
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

DEFAULT_ADDITIONAL_READ_GROUPS: tuple[tuple[int, ...], ...] = (
    ADDITIONAL_DEFAULT_READ_POINTS,
    CONTROL_STATE_READ_POINTS,
    REMAINING_DEFAULT_USER_READ_POINTS,
)

BK_ADDITIONAL_READ_GROUPS: tuple[tuple[int, ...], ...] = (
    REMAINING_BK_USER_READ_POINTS,
)
