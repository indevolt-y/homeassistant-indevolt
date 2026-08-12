from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.entity import EntityCategory


@dataclass(frozen=True, kw_only=True)
class IndevoltSensorEntityDescription(SensorEntityDescription):
    """Custom entity description class for Indevolt sensors."""
    name: str = ""
    value_fn: Callable[[str], float | int | str | None] = lambda value: value
    entity_category: EntityCategory | None = None

def format_firmware_version(version: int | str) -> str:
    """Format firmware version number."""

    v = str(version)

    if len(v) == 5:
        return f"{int(v[0])}.{v[1:3]}.{v[3:5]}"

    elif len(v) == 3:
        return f"{int(v[0])}.{v[1:3]}"

    else:
        return v
