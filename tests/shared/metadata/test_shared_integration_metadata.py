"""Regression tests for the integration metadata exposed to Home Assistant."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from homeassistant.const import Platform

from custom_components.indevolt.const import (
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_REAL_TIME_CONTROL_POWER,
    PLATFORMS,
)

INTEGRATION_ROOT = Path(__file__).parents[3] / "custom_components" / "indevolt"


def test_constants_keep_the_existing_runtime_contract() -> None:
    assert DOMAIN == "indevolt"
    assert DEFAULT_PORT == 8080
    assert DEFAULT_SCAN_INTERVAL == 30
    assert MAX_REAL_TIME_CONTROL_POWER == 10_800
    assert PLATFORMS == [
        Platform.SENSOR,
        Platform.BINARY_SENSOR,
        Platform.SWITCH,
        Platform.NUMBER,
        Platform.SELECT,
        Platform.TIME,
    ]


def test_manifest_keeps_the_existing_home_assistant_contract() -> None:
    manifest = json.loads((INTEGRATION_ROOT / "manifest.json").read_text())

    assert manifest == {
        "domain": "indevolt",
        "name": "INDEVOLT",
        "codeowners": ["@INDEVOLT"],
        "config_flow": True,
        "dependencies": [],
        "documentation": "https://github.com/INDEVOLT/homeassistant-indevolt",
        "integration_type": "hub",
        "iot_class": "local_polling",
        "issue_tracker": "https://github.com/INDEVOLT/homeassistant-indevolt/issues",
        "requirements": ["aiohttp"],
        "version": "1.3",
    }


def test_action_yaml_keeps_the_complete_existing_selector_contract() -> None:
    services = yaml.safe_load((INTEGRATION_ROOT / "services.yaml").read_text())

    assert services == {
        "set_solidflex_powerflex_work_mode": {
            "target": {"device": {"integration": "indevolt"}},
            "fields": {
                "mode": {
                    "required": True,
                    "selector": {
                        "select": {
                            "options": [
                                "Self-Consumed Prioritized",
                                "Real-Time Control",
                                "Charge/Discharge Schedule",
                            ]
                        }
                    },
                },
                "state": {
                    "required": False,
                    "selector": {
                        "select": {"options": ["Standby", "Charging", "Discharging"]}
                    },
                },
                "power": {
                    "required": False,
                    "selector": {
                        "number": {
                            "min": 50,
                            "max": 10_800,
                            "step": 10,
                            "unit_of_measurement": "W",
                        }
                    },
                },
                "soc": {
                    "required": False,
                    "selector": {
                        "number": {
                            "min": 5,
                            "max": 100,
                            "step": 1,
                            "unit_of_measurement": "%",
                        }
                    },
                },
            },
        },
        "set_bk1600_work_mode": {
            "target": {"device": {"integration": "indevolt"}},
            "fields": {
                "mode": {
                    "required": True,
                    "selector": {"select": {"options": ["Real-Time Control"]}},
                },
                "state": {
                    "required": False,
                    "selector": {
                        "select": {"options": ["Standby", "Charging", "Discharging"]}
                    },
                },
                "power": {
                    "required": False,
                    "selector": {
                        "number": {
                            "min": 0,
                            "max": 1200,
                            "step": 10,
                            "unit_of_measurement": "W",
                        }
                    },
                },
                "soc": {
                    "required": False,
                    "selector": {
                        "number": {
                            "min": 0,
                            "max": 100,
                            "step": 1,
                            "unit_of_measurement": "%",
                        }
                    },
                },
            },
        },
    }
