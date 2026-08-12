"""Import-boundary contract for the pure OpenData command package."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

OPEN_DATA_PACKAGE = (
    Path(__file__).parents[4] / "custom_components" / "indevolt" / "opendata"
)


def test_commands_import_without_home_assistant_or_top_level_side_effects() -> None:
    script = f"""
import builtins
import sys

original_import = builtins.__import__

def guarded_import(name, *args, **kwargs):
    if name == "homeassistant" or name.startswith("homeassistant."):
        raise AssertionError(f"unexpected Home Assistant import: {{name}}")
    return original_import(name, *args, **kwargs)

builtins.__import__ = guarded_import
sys.path.insert(0, {str(OPEN_DATA_PACKAGE.parent)!r})
import opendata
assert not any(name.startswith("opendata.commands") for name in sys.modules)
from opendata import commands
from opendata.commands import set_real_time_control_parameters
assert set(commands.__all__) == {{
    "LoadSetting",
    "OpenDataWrite",
    "RealTimeControlState",
    "SetDataRequest",
    "WorkMode",
    "set_backup_soc",
    "set_bypass",
    "set_feed_in_power_limit",
    "set_grid_charging",
    "set_inverter_input_limit",
    "set_light",
    "set_load_setting",
    "set_max_ac_output_power",
    "set_real_time_control_parameters",
    "set_real_time_control_power",
    "set_real_time_control_state",
    "set_real_time_control_target_soc",
    "set_work_mode",
}}
assert not any(
    name.startswith(("BK1600", "SF2000", "PF2000", "FALLBACK"))
    for name in vars(commands)
)
assert set_real_time_control_parameters(1, 1200, 80).as_set_data_request() == {{
    "point": 47015,
    "value": [1, 1200, 80],
}}
"""

    subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
