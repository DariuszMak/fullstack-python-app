import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import httpx
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.backend.api.app import app

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
def test_weather_info_returns_200(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        response = client.post("/api/v1/weather/info", json={})

    assert response.status_code == 200


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_response_has_required_top_level_keys(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    assert "hourly" in data
    assert "daily" in data
    assert "hourly_rows" in data
    assert "daily_rows" in data


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_row_counts_match_dataframes(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(N_HOURS), _make_daily_df(N_DAYS))

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    assert data["hourly_rows"] == N_HOURS
    assert data["daily_rows"] == N_DAYS
    assert len(data["hourly"]) == N_HOURS
    assert len(data["daily"]) == N_DAYS


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_hourly_record_has_all_fields(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    first_hourly = data["hourly"][0]
    for field in HOURLY_COLUMNS:
        assert field in first_hourly, f"missing hourly field: {field}"


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_daily_record_has_all_fields(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    first_daily = data["daily"][0]
    for field in DAILY_COLUMNS:
        assert field in first_daily, f"missing daily field: {field}"


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_hourly_dates_are_iso_strings(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    for record in data["hourly"]:
        dt = datetime.fromisoformat(record["date"])
        assert dt.tzinfo is not None


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_daily_dates_are_iso_strings(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    for record in data["daily"]:
        dt = datetime.fromisoformat(record["date"])
        assert dt.tzinfo is not None


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_sunrise_sunset_are_integers(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    for record in data["daily"]:
        assert isinstance(record["sunrise"], int)
        assert isinstance(record["sunset"], int)


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_passes_params_to_build_request_parameters(
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
        client.post("/api/v1/weather/info", json=payload)

    mock_build.assert_called_once_with(
        latitude=54.352,
        longitude=18.649,
        timezone="Europe/Warsaw",
        forecast_days=7,
    )


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_passes_built_parameters_to_gather_data(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    sentinel_params = {"sentinel": True}
    mock_build.return_value = sentinel_params
    mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

    with TestClient(app) as client:
        client.post("/api/v1/weather/info", json={})

    mock_gather.assert_called_once_with(sentinel_params)


def test_weather_info_default_params_are_valid() -> None:
    with (
        patch("src.backend.api.routes.gather_data") as mock_gather,
        patch("src.backend.api.routes.build_request_parameters") as mock_build,
    ):
        mock_build.return_value = {}
        mock_gather.return_value = (_make_hourly_df(), _make_daily_df())

        with TestClient(app) as client:
            response = client.post("/api/v1/weather/info", json={})

    assert response.status_code == 200


def test_weather_info_rejects_forecast_days_out_of_range() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/weather/info", json={"forecast_days": 0})
    assert response.status_code == 422

    with TestClient(app) as client:
        response = client.post("/api/v1/weather/info", json={"forecast_days": 17})
    assert response.status_code == 422


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_sanitizes_nan_in_hourly(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    hourly_df = _make_hourly_df(1)
    hourly_df.loc[0, "temperature_2m"] = float("nan")
    mock_build.return_value = {}
    mock_gather.return_value = (hourly_df, _make_daily_df(1))

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    assert data["hourly"][0]["temperature_2m"] == pytest.approx(0.0)


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_sanitizes_inf_in_hourly(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    hourly_df = _make_hourly_df(1)
    hourly_df.loc[0, "wind_speed_10m"] = float("inf")
    mock_build.return_value = {}
    mock_gather.return_value = (hourly_df, _make_daily_df(1))

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    assert data["hourly"][0]["wind_speed_10m"] == pytest.approx(0.0)


@patch("src.backend.api.routes.gather_data")
@patch("src.backend.api.routes.build_request_parameters")
def test_weather_info_sanitizes_nan_in_daily(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    daily_df = _make_daily_df(1)
    daily_df.loc[0, "rain_sum"] = float("nan")
    mock_build.return_value = {}
    mock_gather.return_value = (_make_hourly_df(1), daily_df)

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/info", json={}).json()

    assert data["daily"][0]["rain_sum"] == pytest.approx(0.0)
