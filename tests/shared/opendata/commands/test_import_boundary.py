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
from opendata.commands import set_real_time_control_power
assert set(commands.__all__) == {{
    "set_backup_soc",
    "set_feed_in_power_limit",
    "set_inverter_input_limit",
    "set_max_ac_output_power",
    "set_real_time_control_power",
    "set_real_time_control_target_soc",
}}
request = set_real_time_control_power(1200.0).as_set_data_request()
assert request == {{
    "point": 47016,
    "value": [1200.0],
}}
assert type(request["value"][0]) is float
"""

    subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
