"""Resolve Core and custom INDEVOLT config-entry fields at runtime."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL


def normalize_device_model(model: object) -> object:
    """Return the historical custom model label for one device model."""
    if not isinstance(model, str):
        return model
    if "SF2000" in model:
        return "SolidFlex/PowerFlex2000"
    if "BK1600" in model:
        return "BK1600/BK1600Ultra"
    return model


def resolve_entry_config(data: Mapping[str, Any]) -> dict[str, Any]:
    """Build a non-persistent runtime view that accepts both entry schemas."""
    config = dict(data)

    core_model = data.get("model")
    custom_model = data.get("device_model")
    if custom_model is None and core_model is not None:
        custom_model = normalize_device_model(core_model)
    if core_model is None and custom_model is not None:
        core_model = custom_model
    if core_model is not None:
        config["model"] = core_model
    if custom_model is not None:
        config["device_model"] = custom_model

    custom_serial = data.get("sn")
    core_serial = data.get("serial_number")
    if (
        custom_serial is not None
        and core_serial is not None
        and custom_serial != core_serial
    ):
        raise ValueError("Conflicting INDEVOLT serial-number fields")
    serial_number = custom_serial if custom_serial is not None else core_serial
    if serial_number is not None:
        config["sn"] = serial_number
        config["serial_number"] = serial_number

    config.setdefault("port", DEFAULT_PORT)
    config.setdefault("scan_interval", DEFAULT_SCAN_INTERVAL)
    return config


def runtime_config(coordinator: object) -> Mapping[str, Any]:
    """Return resolved config, falling back for lightweight test doubles."""
    config = getattr(coordinator, "config", None)
    if isinstance(config, Mapping):
        return config

    entry = getattr(coordinator, "config_entry", None)
    data = getattr(entry, "data", None)
    if isinstance(data, Mapping):
        return resolve_entry_config(data)
    return {}


def runtime_device_model(coordinator: object) -> str:
    """Return the required custom runtime model."""
    model = runtime_config(coordinator).get("device_model")
    if not isinstance(model, str) or not model:
        raise ValueError("INDEVOLT device model is missing")
    return model


def runtime_serial_number(coordinator: object) -> str:
    """Return the required runtime serial number."""
    serial_number = runtime_config(coordinator).get("sn")
    if not isinstance(serial_number, str) or not serial_number:
        raise ValueError("INDEVOLT serial number is missing")
    return serial_number


def runtime_firmware_version(coordinator: object) -> str | None:
    """Return an optional firmware version from custom entries."""
    firmware_version = runtime_config(coordinator).get("fw_version")
    return firmware_version if isinstance(firmware_version, str) else None
