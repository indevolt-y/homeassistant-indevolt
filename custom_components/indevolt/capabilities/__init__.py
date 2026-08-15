"""Declarative Home Assistant capabilities for documented OpenData points."""

from .definitions import GetUserCapability
from .reads import BK_GET_USER_CAPABILITIES, GET_USER_CAPABILITIES

__all__ = (
    "BK_GET_USER_CAPABILITIES",
    "GET_USER_CAPABILITIES",
    "GetUserCapability",
)
