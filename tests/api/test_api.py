import asyncio
from datetime import UTC, datetime

import httpx
import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.routes import set_time_sync_context
from src.api.time_provider.time_provider import (
    AisenseApiProvider,
    GettimeApiProvider,
    HttpTimeProvider,
    LocalTimeProvider,
    TimeProvider,
    TimeSyncContext,
    default_time_sync_context,
)


def test_chrome_devtools_json_not_found() -> None:
    with TestClient(app) as client:
        response = client.get("/.well-known/appspecific/com.chrome.devtools.json")
        assert response.status_code == 204


def test_redoc_available() -> None:
    with TestClient(app) as client:
        resp = client.get("/redoc")
        assert resp.status_code == 200
        assert "html" in resp.headers["content-type"]


def test_swagger_ui_available() -> None:
    with TestClient(app) as client:
        resp = client.get("/docs")
        assert resp.status_code == 200
        assert "html" in resp.headers["content-type"]


def test_favicon() -> None:
    with TestClient(app) as client:
        response = client.get("/favicon.ico")
        assert response.status_code == 200


def test_ping_route() -> None:
    with TestClient(app) as client:
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"message": "pong"}


def _assert_datetime_response(data: dict[str, str]) -> datetime:
    assert "datetime" in data
    dt = datetime.fromisoformat(data["datetime"])
    assert dt.tzinfo is not None
    return dt


@pytest.mark.asyncio
async def test_local_time_provider_always_succeeds() -> None:
    provider = LocalTimeProvider()
    result = await provider.fetch_time()
    assert result is not None
    assert result.tzinfo is not None


@pytest.mark.asyncio
async def test_http_provider_returns_none_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def mock_get(self: httpx.AsyncClient, url: str) -> None:
        await asyncio.sleep(0)
        raise httpx.ConnectError("no internet")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    provider = GettimeApiProvider()
    result = await provider.fetch_time()
    assert result is None


@pytest.mark.asyncio
async def test_http_provider_returns_none_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Resp:
        def json(self) -> dict[str, str]:
            return {"unexpected_key": "value"}

        def raise_for_status(self) -> None:
            pass

    async def mock_get(self: httpx.AsyncClient, url: str) -> _Resp:
        await asyncio.sleep(0)
        return _Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    provider = GettimeApiProvider()
    result = await provider.fetch_time()
    assert result is None


@pytest.mark.asyncio
async def test_gettime_api_provider_parses_iso8601_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    iso_time = "2025-06-15T08:30:00+00:00"

    class _Resp:
        def json(self) -> dict[str, str]:
            return {"iso8601": iso_time}

        def raise_for_status(self) -> None:
            pass

    async def mock_get(self: httpx.AsyncClient, url: str) -> _Resp:
        await asyncio.sleep(0)
        return _Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    provider = GettimeApiProvider()
    result = await provider.fetch_time()
    assert result is not None
    assert result.astimezone(UTC) == datetime.fromisoformat(iso_time)


@pytest.mark.asyncio
async def test_aisense_api_provider_parses_datetime_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    iso_time = "2025-06-15T08:30:00+00:00"

    class _Resp:
        def json(self) -> dict[str, str]:
            return {"datetime": iso_time}

        def raise_for_status(self) -> None:
            pass

    async def mock_get(self: httpx.AsyncClient, url: str) -> _Resp:
        await asyncio.sleep(0)
        return _Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    provider = AisenseApiProvider()
    result = await provider.fetch_time()
    assert result is not None
    assert result.astimezone(UTC) == datetime.fromisoformat(iso_time)


@pytest.mark.asyncio
async def test_context_uses_first_successful_provider() -> None:
    fixed_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    call_order: list[str] = []

    class _SuccessProvider(HttpTimeProvider):
        def __init__(self, name: str) -> None:
            self._name = name

        async def fetch_time(self) -> datetime:
            call_order.append(self._name)
            return fixed_time

    class _FailProvider(HttpTimeProvider):
        def __init__(self, name: str) -> None:
            self._name = name

        async def fetch_time(self) -> datetime | None:
            call_order.append(self._name)
            return None

    context = TimeSyncContext(
        providers=[
            _FailProvider("first"),
            _SuccessProvider("second"),
            _SuccessProvider("third"),
        ]
    )
    result = await context.get_current_time()

    assert result == fixed_time
    assert call_order == ["first", "second"]


@pytest.mark.asyncio
async def test_context_falls_back_to_local_when_all_http_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def mock_get(self: httpx.AsyncClient, url: str) -> None:
        await asyncio.sleep(0)
        raise httpx.ConnectError("no internet")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    context = TimeSyncContext(
        providers=[
            GettimeApiProvider(),
            AisenseApiProvider(),
            LocalTimeProvider(),
        ]
    )
    result = await context.get_current_time()
    assert result.tzinfo is not None


def test_context_raises_when_no_providers_configured() -> None:
    with pytest.raises(ValueError, match="At least one TimeProvider is required"):
        TimeSyncContext(providers=[])


def test_time_route_returns_aware_datetime() -> None:
    with TestClient(app) as client:
        response = client.get("/time")

    assert response.status_code == 200
    _assert_datetime_response(response.json())


def test_time_route_uses_injected_context() -> None:
    fixed_utc = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

    class _FixedProvider(TimeProvider):
        async def fetch_time(self) -> datetime:
            return fixed_utc

    set_time_sync_context(TimeSyncContext(providers=[_FixedProvider()]))

    try:
        with TestClient(app) as client:
            response = client.get("/time")

        assert response.status_code == 200
        data = response.json()
        dt = datetime.fromisoformat(data["datetime"]).astimezone(UTC)
        assert dt == fixed_utc
    finally:
        set_time_sync_context(default_time_sync_context())


def test_time_route_remote_via_monkeypatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_utc_time = "2025-01-01T12:00:00+00:00"

    class _Resp:
        def json(self) -> dict[str, str]:
            return {"iso8601": api_utc_time}

        def raise_for_status(self) -> None:
            pass

    async def mock_get(self: httpx.AsyncClient, url: str) -> _Resp:
        await asyncio.sleep(0)
        return _Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with TestClient(app) as client:
        response = client.get("/time")

    assert response.status_code == 200
    dt = _assert_datetime_response(response.json())
    assert dt.astimezone(UTC) == datetime.fromisoformat(api_utc_time)


def test_time_route_fallback_to_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def mock_get(self: httpx.AsyncClient, url: str) -> None:
        await asyncio.sleep(0)
        raise httpx.ConnectError("no internet")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with TestClient(app) as client:
        response = client.get("/time")

    assert response.status_code == 200
    _assert_datetime_response(response.json())
