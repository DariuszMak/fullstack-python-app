import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import httpx
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.backend.api.app import app
from src.backend.api.routes import _sanitize_float, set_time_sync_context
from src.backend.api.time_provider.context import default_time_sync_context
from src.backend.api.time_provider.strategy.ai_sense_api import AiSenseApi
from src.backend.api.time_provider.strategy.get_time_api import GetTimeApi
from src.backend.api.time_provider.strategy.interface.http_time_provider import HttpTimeProvider
from src.backend.api.time_provider.strategy.interface.time_provider import TimeProvider
from src.backend.api.time_provider.strategy.local_time import LocalTime
from src.backend.api.time_provider.time_sync_context import TimeSyncContext
from src.backend.openmeteo.gather import gather_data
from tests.backend.openmeteo.test_openmeto import _make_daily_mock, _make_hourly_mock

N_HOURS = 384
N_DAYS = 16
UTC_OFFSET = 7200

START_TS = int(pd.Timestamp("2026-05-22", tz="UTC").timestamp())
END_TS_HOURLY = START_TS + N_HOURS * 3600
END_TS_DAILY = START_TS + N_DAYS * 86400


HOURLY_PREVIEW = {
    "date": "2026-05-22T00:00:00+00:00",
    "temperature_2m": 11.911,
    "cloud_cover": 66.0,
    "precipitation": 0.0,
    "apparent_temperature": 10.955,
    "soil_temperature_6cm": 12.411,
    "relative_humidity_2m": 78.0,
    "surface_pressure": 1012.826,
    "wind_speed_10m": 3.319,
    "wind_direction_10m": 220.601,
    "wind_gusts_10m": 7.92,
    "soil_moisture_0_to_1cm": 0.238,
}

DAILY_PREVIEW = {
    "date": "2026-05-22T00:00:00+00:00",
    "sunshine_duration": 48861.777,
    "uv_index_max": 5.75,
    "apparent_temperature_max": 19.392,
    "apparent_temperature_min": 8.922,
    "sunrise": 1779417972,
    "sunset": 1779475626,
    "daylight_duration": 57648.105,
    "rain_sum": 0.0,
    "temperature_2m_max": 21.111,
    "temperature_2m_min": 10.061,
}

HOURLY_COLUMNS = [
    "date",
    "temperature_2m",
    "cloud_cover",
    "precipitation",
    "apparent_temperature",
    "soil_temperature_6cm",
    "relative_humidity_2m",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "soil_moisture_0_to_1cm",
]

DAILY_COLUMNS = [
    "date",
    "sunshine_duration",
    "uv_index_max",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "sunrise",
    "sunset",
    "daylight_duration",
    "rain_sum",
    "temperature_2m_max",
    "temperature_2m_min",
]


def _make_hourly_df(n: int = N_HOURS) -> pd.DataFrame:
    dates = pd.date_range(
        start=pd.Timestamp("2026-05-22", tz="UTC"),
        periods=n,
        freq="h",
    )
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "date": dates,
        "temperature_2m": rng.uniform(5.0, 30.0, n).astype(np.float32),
        "cloud_cover": rng.uniform(0.0, 100.0, n).astype(np.float32),
        "precipitation": rng.uniform(0.0, 5.0, n).astype(np.float32),
        "apparent_temperature": rng.uniform(3.0, 28.0, n).astype(np.float32),
        "soil_temperature_6cm": rng.uniform(5.0, 25.0, n).astype(np.float32),
        "relative_humidity_2m": rng.uniform(30.0, 100.0, n).astype(np.float32),
        "surface_pressure": rng.uniform(980.0, 1030.0, n).astype(np.float32),
        "wind_speed_10m": rng.uniform(0.0, 20.0, n).astype(np.float32),
        "wind_direction_10m": rng.uniform(0.0, 360.0, n).astype(np.float32),
        "wind_gusts_10m": rng.uniform(0.0, 40.0, n).astype(np.float32),
        "soil_moisture_0_to_1cm": rng.uniform(0.0, 0.5, n).astype(np.float32),
    })


def _make_daily_df(n: int = N_DAYS) -> pd.DataFrame:
    dates = pd.date_range(
        start=pd.Timestamp("2026-05-22", tz="UTC"),
        periods=n,
        freq="D",
    )
    rng = np.random.default_rng(42)
    base_ts = START_TS
    return pd.DataFrame({
        "date": dates,
        "sunshine_duration": rng.uniform(0.0, 86400.0, n).astype(np.float32),
        "uv_index_max": rng.uniform(0.0, 12.0, n).astype(np.float32),
        "apparent_temperature_max": rng.uniform(10.0, 35.0, n).astype(np.float32),
        "apparent_temperature_min": rng.uniform(0.0, 15.0, n).astype(np.float32),
        "sunrise": np.array([base_ts + i * 86400 + 18000 for i in range(n)], dtype=np.int64),
        "sunset": np.array([base_ts + i * 86400 + 75600 for i in range(n)], dtype=np.int64),
        "daylight_duration": rng.uniform(30000.0, 60000.0, n).astype(np.float32),
        "rain_sum": rng.uniform(0.0, 20.0, n).astype(np.float32),
        "temperature_2m_max": rng.uniform(10.0, 35.0, n).astype(np.float32),
        "temperature_2m_min": rng.uniform(0.0, 15.0, n).astype(np.float32),
    })


def _assert_datetime_response(data: dict[str, str]) -> datetime:
    assert "datetime" in data
    dt = datetime.fromisoformat(data["datetime"])
    assert dt.tzinfo is not None
    return dt


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


@pytest.mark.asyncio
async def test_local_time_provider_always_succeeds() -> None:
    provider = LocalTime()
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
    provider = GetTimeApi()
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
    provider = GetTimeApi()
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
    provider = GetTimeApi()
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
    provider = AiSenseApi()
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

    context = TimeSyncContext(providers=[GetTimeApi(), AiSenseApi(), LocalTime()])
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


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_returns_200(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        response = client.post("/api/v1/weather/calculate", json={})

    assert response.status_code == 200


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_response_has_required_top_level_keys(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    assert "hourly" in data
    assert "daily" in data
    assert "hourly_rows" in data
    assert "daily_rows" in data


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_row_counts_match_dataframes(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(N_HOURS), _make_daily_df(N_DAYS))

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    assert data["hourly_rows"] == N_HOURS
    assert data["daily_rows"] == N_DAYS
    assert len(data["hourly"]) == N_HOURS
    assert len(data["daily"]) == N_DAYS


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_hourly_record_has_all_fields(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    first_hourly = data["hourly"][0]
    for field in HOURLY_COLUMNS:
        assert field in first_hourly, f"missing hourly field: {field}"


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_daily_record_has_all_fields(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    first_daily = data["daily"][0]
    for field in DAILY_COLUMNS:
        assert field in first_daily, f"missing daily field: {field}"


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_hourly_dates_are_iso_strings(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    for record in data["hourly"]:
        dt = datetime.fromisoformat(record["date"])
        assert dt.tzinfo is not None


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_daily_dates_are_iso_strings(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    for record in data["daily"]:
        dt = datetime.fromisoformat(record["date"])
        assert dt.tzinfo is not None


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_sunrise_sunset_are_integers(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    for record in data["daily"]:
        assert isinstance(record["sunrise"], int)
        assert isinstance(record["sunset"], int)


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_passes_params_to_build_request_parameters(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    payload = {
        "latitude": 54.352,
        "longitude": 18.649,
        "timezone": "Europe/Warsaw",
        "forecast_days": 7,
    }

    with TestClient(app) as client:
        client.post("/api/v1/weather/calculate", json=payload)

    mock_build.assert_called_once_with(
        latitude=54.352,
        longitude=18.649,
        timezone="Europe/Warsaw",
        forecast_days=7,
    )


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_passes_built_parameters_to_gather_data(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    sentinel_params = {"sentinel": True}
    mock_build.return_value = sentinel_params
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        client.post("/api/v1/weather/calculate", json={})

    mock_gather.assert_called_once_with(sentinel_params)


def test_weather_calculate_default_params_are_valid() -> None:
    """Empty body should use defaults without validation error."""
    with (
        patch("src.backend.api.routes.gather_data") as mock_gather,
        patch("src.backend.api.routes.build_request_parameters") as mock_build,
    ):
        mock_build.return_value = {}
        mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

        with TestClient(app) as client:
            response = client.post("/api/v1/weather/calculate", json={})

    assert response.status_code == 200


def test_weather_calculate_rejects_forecast_days_out_of_range() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/weather/calculate", json={"forecast_days": 0})
    assert response.status_code == 422

    with TestClient(app) as client:
        response = client.post("/api/v1/weather/calculate", json={"forecast_days": 17})
    assert response.status_code == 422


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_sanitizes_nan_in_hourly(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    hourly_df = _make_hourly_df(1)
    hourly_df.loc[0, "temperature_2m"] = float("nan")
    mock_build.return_value = {}
    mock_gather.return_value = (hourly_df, _make_daily_df(1))

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    assert data["hourly"][0]["temperature_2m"] == 0.0


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_sanitizes_inf_in_hourly(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    hourly_df = _make_hourly_df(1)
    hourly_df.loc[0, "wind_speed_10m"] = float("inf")
    mock_build.return_value = {}
    mock_gather.return_value = (hourly_df, _make_daily_df(1))

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    assert data["hourly"][0]["wind_speed_10m"] == 0.0


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_calculate_sanitizes_nan_in_daily(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    daily_df = _make_daily_df(1)
    daily_df.loc[0, "rain_sum"] = float("nan")
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(1), daily_df)

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/calculate", json={}).json()

    assert data["daily"][0]["rain_sum"] == 0.0


def test_sanitize_float_passes_normal_values() -> None:
    assert _sanitize_float(3.14) == pytest.approx(3.14)
    assert _sanitize_float(0.0) == 0.0
    assert _sanitize_float(-273.15) == pytest.approx(-273.15)


def test_sanitize_float_replaces_nan() -> None:
    assert _sanitize_float(float("nan")) == 0.0


def test_sanitize_float_replaces_inf() -> None:
    assert _sanitize_float(float("inf")) == 0.0
    assert _sanitize_float(float("-inf")) == 0.0


@patch("src.backend.openmeteo.gather.build_openmeteo_client")
@patch("src.backend.openmeteo.gather._fetch_weather_response")
def test_gather_data_uses_provided_parameters(
    mock_fetch: MagicMock,
    mock_client: MagicMock,
) -> None:
    response_mock = MagicMock()
    response_mock.UtcOffsetSeconds.return_value = UTC_OFFSET

    response_mock.Hourly.return_value = _make_hourly_mock()
    response_mock.Daily.return_value = _make_daily_mock()
    mock_fetch.return_value = response_mock

    custom_params = {"latitude": 54.352, "longitude": 18.649, "timezone": "Europe/Warsaw"}
    gather_data(custom_params)

    mock_fetch.assert_called_once()
    _, call_kwargs = mock_fetch.call_args
    assert custom_params in mock_fetch.call_args[0] or call_kwargs.get("parameters") == custom_params


@patch("src.backend.openmeteo.gather.build_request_parameters")
@patch("src.backend.openmeteo.gather.build_openmeteo_client")
@patch("src.backend.openmeteo.gather._fetch_weather_response")
def test_gather_data_uses_defaults_when_no_parameters_given(
    mock_fetch: MagicMock,
    mock_client: MagicMock,
    mock_build: MagicMock,
) -> None:
    mock_build.return_value = {"default": True}
    response_mock = MagicMock()
    response_mock.UtcOffsetSeconds.return_value = UTC_OFFSET

    response_mock.Hourly.return_value = _make_hourly_mock()
    response_mock.Daily.return_value = _make_daily_mock()
    mock_fetch.return_value = response_mock

    gather_data()
    mock_build.assert_called_once()
