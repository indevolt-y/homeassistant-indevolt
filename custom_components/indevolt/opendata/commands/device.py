"""Existing load, light, grid-charging, and bypass write commands."""

from __future__ import annotations

from enum import IntEnum

from .request import OpenDataWrite, write_boolean, write_values


class LoadSetting(IntEnum):
    """Raw values currently written for load setting."""

    SMART_PLUG = 1
    METER = 2
    KEY_LOAD = 3
    CUSTOM = 4


def set_load_setting(value: LoadSetting) -> OpenDataWrite:
    """Set load handling using the existing point 1 write."""
    return write_values(1, value)


def set_light(active: bool) -> OpenDataWrite:
    """Enable or disable the device light."""
    return write_boolean(7265, active)


def set_grid_charging(active: bool) -> OpenDataWrite:
    """Enable or disable grid charging."""
    return write_boolean(1143, active)


def set_bypass(active: bool) -> OpenDataWrite:
    """Enable or disable bypass mode."""
    return write_boolean(7266, active)
