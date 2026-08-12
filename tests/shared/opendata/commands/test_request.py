"""Contracts for generic OpenData SetData request encoding."""

from __future__ import annotations

import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

OPEN_DATA_PACKAGE = (
    Path(__file__).parents[4] / "custom_components" / "indevolt" / "opendata"
)
sys.path.insert(0, str(OPEN_DATA_PACKAGE.parent))
try:
    request = importlib.import_module("opendata.commands.request")
finally:
    sys.path.pop(0)


def test_write_is_immutable_and_returns_a_fresh_list_payload() -> None:
    write = request.write_values(47016, 1200)

    with pytest.raises(FrozenInstanceError):
        write.point = 47015

    first_request = write.as_set_data_request()
    first_request["value"].append(80)
    assert write.as_set_data_request() == {"point": 47016, "value": [1200]}


def test_value_encoder_preserves_order_and_rejects_non_integer_values() -> None:
    assert request.write_values(47015, 1, 1200, 80).as_set_data_request() == {
        "point": 47015,
        "value": [1, 1200, 80],
    }

    with pytest.raises(ValueError):
        request.write_values(47015)
    with pytest.raises(TypeError):
        request.write_values(47015, True)


def test_boolean_encoder_uses_the_existing_one_zero_convention() -> None:
    assert request.write_boolean(7265, True).as_set_data_request() == {
        "point": 7265,
        "value": [1],
    }
    assert request.write_boolean(7265, False).as_set_data_request() == {
        "point": 7265,
        "value": [0],
    }

    with pytest.raises(TypeError):
        request.write_boolean(7265, 1)
