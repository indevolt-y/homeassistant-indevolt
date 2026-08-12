"""Model-specific OpenData response definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class OpenDataField:
    """A response field proven by the current polling contract."""

    point: int
    response_key: str


def _fields(*points: int) -> tuple[OpenDataField, ...]:
    """Build immutable response fields without inventing protocol metadata."""
    return tuple(
        OpenDataField(point=point, response_key=str(point)) for point in points
    )


BK1600_SCHEMA: Final[tuple[OpenDataField, ...]] = _fields(
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
)

# BK1600 and BK1600 Ultra are confirmed to use one point table.
BK1600_ULTRA_SCHEMA: Final[tuple[OpenDataField, ...]] = BK1600_SCHEMA

SF2000_SCHEMA: Final[tuple[OpenDataField, ...]] = _fields(
    142,
    606,
    667,
    680,
    1118,
    1109,
    1119,
    1120,
    1136,
    1137,
    1138,
    1139,
    1140,
    1141,
    1142,
    1143,
    1098,
    1099,
    1501,
    1502,
    1600,
    1601,
    1602,
    1603,
    1632,
    1633,
    1634,
    1635,
    1664,
    1665,
    1666,
    1667,
    2101,
    2104,
    2105,
    2107,
    2108,
    2600,
    2612,
    2618,
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
    7171,
    9000,
    9004,
    9008,
    9009,
    9011,
    9012,
    9013,
    9016,
    9020,
    9021,
    9023,
    9030,
    9032,
    9035,
    9039,
    9040,
    9042,
    9049,
    9051,
    9054,
    9058,
    9059,
    9061,
    9068,
    9070,
    9149,
    9153,
    9154,
    9156,
    9163,
    9165,
    9202,
    9206,
    9216,
    9218,
    9219,
    9222,
    11009,
    11010,
    11011,
    11016,
    11034,
    19173,
    19174,
    19175,
    19176,
    19177,
)

# SF2000 and PF2000 are confirmed to use one point table.
PF2000_SCHEMA: Final[tuple[OpenDataField, ...]] = SF2000_SCHEMA

# A model without an explicitly registered point table keeps the current
# non-BK behavior and uses the SF2000 table. Model registration is introduced
# in a later V1.3.18 subversion.
FALLBACK_SCHEMA: Final[tuple[OpenDataField, ...]] = SF2000_SCHEMA
