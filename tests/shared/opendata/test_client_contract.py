"""Contract tests for the Home Assistant-independent OpenData client."""

from __future__ import annotations

import asyncio
import importlib
import subprocess
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp
import pytest

OPEN_DATA_PACKAGE = (
    Path(__file__).parents[3] / "custom_components" / "indevolt" / "opendata"
)
sys.path.insert(0, str(OPEN_DATA_PACKAGE.parent))
try:
    IndevoltAPI = importlib.import_module("opendata").IndevoltAPI
finally:
    sys.path.pop(0)


@dataclass(frozen=True)
class RecordedRequest:
    """HTTP request recorded before a fake response is returned."""

    method: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class FakeResponse:
    """Minimal aiohttp response contract used by the client."""

    def __init__(self, payload: Any, status: int) -> None:
        self.payload = payload
        self.status = status

    async def json(self) -> Any:
        return self.payload


class FailingJSONResponse(FakeResponse):
    """Raise the configured parser error from response.json()."""

    def __init__(self, error: Exception) -> None:
        super().__init__(None, 200)
        self.error = error

    async def json(self) -> Any:
        raise self.error


class FakeRequestContext:
    """Async request context returned by the recording session."""

    def __init__(self, response: FakeResponse, error: BaseException | None) -> None:
        self.response = response
        self.error = error

    async def __aenter__(self) -> FakeResponse:
        if self.error is not None:
            raise self.error
        return self.response

    async def __aexit__(self, *args: Any) -> None:
        return None


class RecordingSession:
    """Record the exact ClientSession calls made by the OpenData client."""

    def __init__(
        self,
        payload: Any,
        *,
        status: int = 200,
        error: BaseException | None = None,
    ) -> None:
        self.response = FakeResponse(payload, status)
        self.error = error
        self.requests: list[RecordedRequest] = []

    def post(self, *args: Any, **kwargs: Any) -> FakeRequestContext:
        return self._request("POST", args, kwargs)

    def get(self, *args: Any, **kwargs: Any) -> FakeRequestContext:
        return self._request("GET", args, kwargs)

    def _request(
        self,
        method: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> FakeRequestContext:
        self.requests.append(RecordedRequest(method, args, kwargs))
        return FakeRequestContext(self.response, self.error)


def make_api(session: RecordingSession) -> IndevoltAPI:
    """Create the client without requiring a real aiohttp session."""
    return IndevoltAPI("192.0.2.10", 80, session)  # type: ignore[arg-type]


def test_opendata_package_imports_without_home_assistant() -> None:
    """The extractable package must not import Home Assistant."""
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
from opendata import IndevoltAPI
assert IndevoltAPI.__module__ == "opendata.client"
"""

    subprocess.run(
        [sys.executable, "-I", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.asyncio
async def test_fetch_data_request_and_return_contract() -> None:
    payload = {"1501": 100, "6001": 1001}
    session = RecordingSession(payload)
    api = make_api(session)

    result = await api.fetch_data([1501, 6001])

    assert result is payload
    assert api.base_url == "http://192.0.2.10:80/rpc"
    assert api.timeout.total == 60
    assert session.requests == [
        RecordedRequest(
            "POST",
            ('http://192.0.2.10:80/rpc/Indevolt.GetData?config={"t":[1501,6001]}',),
            {"timeout": api.timeout},
        )
    ]


@pytest.mark.asyncio
async def test_set_data_request_and_return_contract() -> None:
    session = RecordingSession({"result": 1})
    api = make_api(session)

    result = await api.set_data(point=47015, value=[1, 1200, 80])

    assert result is True
    assert session.requests == [
        RecordedRequest(
            "POST",
            (
                "http://192.0.2.10:80/rpc/Indevolt.SetData?"
                'config={"f":16,"t":47015,"v":[1,1200,80]}',
            ),
            {"timeout": api.timeout},
        )
    ]


@pytest.mark.asyncio
async def test_set_data_preserves_home_assistant_number_float_payload() -> None:
    session = RecordingSession({"result": True})
    api = make_api(session)

    result = await api.set_data(point=47016, value=[1200.0])

    assert result is True
    assert session.requests == [
        RecordedRequest(
            "POST",
            (
                "http://192.0.2.10:80/rpc/Indevolt.SetData?"
                'config={"f":16,"t":47016,"v":[1200.0]}',
            ),
            {"timeout": api.timeout},
        )
    ]


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({}, False),
        ({"result": None}, False),
        ({"result": 0}, False),
        ({"result": False}, False),
        ({"result": []}, False),
        ({"result": 1}, True),
        ({"result": "false"}, True),
    ],
)
@pytest.mark.asyncio
async def test_set_data_keeps_existing_result_truthiness(payload, expected) -> None:
    api = make_api(RecordingSession(payload))

    assert await api.set_data(point=47016, value=[800]) is expected


@pytest.mark.asyncio
async def test_fetch_data_preserves_empty_point_request() -> None:
    session = RecordingSession({})
    api = make_api(session)

    assert await api.fetch_data([]) == {}
    assert session.requests[0].args == (
        'http://192.0.2.10:80/rpc/Indevolt.GetData?config={"t":[]}',
    )


@pytest.mark.asyncio
async def test_get_config_request_and_return_contract() -> None:
    payload = {"device": {"type": "BK1600", "sn": "test-sn"}}
    session = RecordingSession(payload)
    api = make_api(session)

    result = await api.get_config()

    assert result is payload
    assert session.requests == [
        RecordedRequest(
            "GET",
            (),
            {
                "url": "http://192.0.2.10:80/rpc/Sys.GetConfig",
                "timeout": api.timeout,
            },
        )
    ]


ClientCall = Callable[[IndevoltAPI], Awaitable[Any]]


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda api: api.fetch_data([1501]), "HTTP status error: 503"),
        (lambda api: api.set_data(47016, [800]), "HTTP status error: 503"),
        (lambda api: api.get_config(), "HTTP status error: 503"),
    ],
)
@pytest.mark.asyncio
async def test_http_status_error_contract(call: ClientCall, message: str) -> None:
    api = make_api(RecordingSession({}, status=503))

    with pytest.raises(Exception, match=f"^{message}$"):
        await call(api)


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda api: api.fetch_data([1501]), "Indevolt.GetData Request timed out"),
        (lambda api: api.set_data(47016, [800]), "Indevolt.SetData Request timed out"),
        (lambda api: api.get_config(), "Indevolt Sys.GetConfig Request timed out"),
    ],
)
@pytest.mark.asyncio
async def test_timeout_error_contract(call: ClientCall, message: str) -> None:
    api = make_api(RecordingSession({}, error=asyncio.TimeoutError()))

    with pytest.raises(Exception, match=f"^{message}$"):
        await call(api)


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda api: api.fetch_data([1501]),
            "Indevolt.GetData Network error: disconnected",
        ),
        (
            lambda api: api.set_data(47016, [800]),
            "Indevolt.SetData Network error: disconnected",
        ),
        (
            lambda api: api.get_config(),
            "Indevolt Sys.GetConfig Network error: disconnected",
        ),
    ],
)
@pytest.mark.asyncio
async def test_network_error_contract(call: ClientCall, message: str) -> None:
    error = aiohttp.ClientConnectionError("disconnected")
    api = make_api(RecordingSession({}, error=error))

    with pytest.raises(Exception, match=f"^{message}$"):
        await call(api)


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.fetch_data([1501]),
        lambda api: api.set_data(47016, [800]),
        lambda api: api.get_config(),
    ],
)
@pytest.mark.asyncio
async def test_json_decode_errors_are_not_rewritten(call: ClientCall) -> None:
    session = RecordingSession({})
    session.response = FailingJSONResponse(ValueError("invalid json"))
    api = make_api(session)

    with pytest.raises(ValueError, match="^invalid json$"):
        await call(api)
