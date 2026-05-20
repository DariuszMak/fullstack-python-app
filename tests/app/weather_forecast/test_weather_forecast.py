from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.app.openmeteo.client_builder import build_openmeteo_client
from src.app.openmeteo.fetch import fetch_weather_response
from src.app.openmeteo.gather import gather_data
from src.app.openmeteo.parameters import (
    FORECAST_DAYS,
    LATITUDE,
    LONGITUDE,
    TIMEZONE,
    build_request_parameters,
)
from src.app.openmeteo.parser import (
    parse_daily_dataframe,
    parse_hourly_dataframe,
)

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

N_HOURS = 24
N_DAYS = 3
UTC_OFFSET = 3600

START_TS = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp())
END_TS_HOURLY = START_TS + N_HOURS * 3600
END_TS_DAILY = START_TS + N_DAYS * 86400


def _make_variables_mock(values_list: list[np.ndarray], *, integer: bool = False) -> MagicMock:
    var_mocks = []
    for arr in values_list:
        v = MagicMock()
        if integer:
            v.ValuesInt64AsNumpy.return_value = arr
        else:
            v.ValuesAsNumpy.return_value = arr
        var_mocks.append(v)

    container = MagicMock()
    container.Variables.side_effect = lambda i: var_mocks[i]
    return container


def _make_hourly_mock(n: int = N_HOURS) -> MagicMock:
    arrays = [np.random.rand(n).astype(np.float32) for _ in range(11)]
    mock = _make_variables_mock(arrays)
    mock.Time.return_value = START_TS - UTC_OFFSET
    mock.TimeEnd.return_value = END_TS_HOURLY - UTC_OFFSET
    mock.Interval.return_value = 3600
    return mock


def _make_daily_mock(n: int = N_DAYS) -> MagicMock:
    float_arrays = [np.random.rand(n).astype(np.float32) for _ in range(8)]
    int_arrays = [np.random.randint(0, 86400, n, dtype=np.int64) for _ in range(2)]

    all_arrays = float_arrays[:4] + int_arrays + float_arrays[4:]

    mock = MagicMock()

    var_mocks = []
    for idx, arr in enumerate(all_arrays):
        v = MagicMock()
        if idx in (4, 5):
            v.ValuesInt64AsNumpy.return_value = arr
        else:
            v.ValuesAsNumpy.return_value = arr
        var_mocks.append(v)

    mock.Variables.side_effect = lambda i: var_mocks[i]
    mock.Time.return_value = START_TS - UTC_OFFSET
    mock.TimeEnd.return_value = END_TS_DAILY - UTC_OFFSET
    mock.Interval.return_value = 86400
    return mock


def test_returns_required_keys() -> None:
    parameters = build_request_parameters()
    for key in ("latitude", "longitude", "daily", "hourly", "timezone", "forecast_days"):
        assert key in parameters


def test_default_coordinates() -> None:
    parameters = build_request_parameters()
    assert parameters["latitude"] == LATITUDE
    assert parameters["longitude"] == LONGITUDE


def test_custom_coordinates() -> None:
    parameters = build_request_parameters(latitude=52.0, longitude=18.0)
    assert parameters["latitude"] == pytest.approx(52.0)
    assert parameters["longitude"] == pytest.approx(18.0)


def test_daily_and_hourly_are_lists() -> None:
    parameters = build_request_parameters()
    assert isinstance(parameters["daily"], list)
    assert isinstance(parameters["hourly"], list)
    assert len(parameters["daily"]) > 0
    assert len(parameters["hourly"]) > 0


def test_forecast_days_default() -> None:
    assert build_request_parameters()["forecast_days"] == FORECAST_DAYS


def test_custom_forecast_days() -> None:
    assert build_request_parameters(forecast_days=7)["forecast_days"] == 7


def test_timezone_default() -> None:
    assert build_request_parameters()["timezone"] == TIMEZONE


@patch("src.app.openmeteo.client_builder.openmeteo_requests.Client")
@patch("src.app.openmeteo.client_builder.retry")
@patch("src.app.openmeteo.client_builder.requests_cache.CachedSession")
def test_returns_client(mock_session: MagicMock, mock_retry: MagicMock, mock_client_cls: MagicMock) -> None:
    client = build_openmeteo_client()
    mock_client_cls.assert_called_once()
    assert client is mock_client_cls.return_value


@patch("src.app.openmeteo.client_builder.openmeteo_requests.Client")
@patch("src.app.openmeteo.client_builder.retry")
@patch("src.app.openmeteo.client_builder.requests_cache.CachedSession")
def test_cache_parameters_forwarded(mock_session: MagicMock, mock_retry: MagicMock, mock_client_cls: MagicMock) -> None:
    build_openmeteo_client(cache_name="custom", expire_after=999)
    mock_session.assert_called_once_with("custom", expire_after=999)


@patch("src.app.openmeteo.client_builder.openmeteo_requests.Client")
@patch("src.app.openmeteo.client_builder.retry")
@patch("src.app.openmeteo.client_builder.requests_cache.CachedSession")
def test_retry_parameters_forwarded(mock_session: MagicMock, mock_retry: MagicMock, mock_client_cls: MagicMock) -> None:
    build_openmeteo_client(retries=3, backoff_factor=0.5)
    mock_retry.assert_called_once_with(mock_session.return_value, retries=3, backoff_factor=0.5)


def test_returns_hourly_dataframe() -> None:
    df = parse_hourly_dataframe(_make_hourly_mock(), UTC_OFFSET)
    assert isinstance(df, pd.DataFrame)


def test_has_correct_hourly_columns() -> None:
    df = parse_hourly_dataframe(_make_hourly_mock(), UTC_OFFSET)
    assert list(df.columns) == HOURLY_COLUMNS


def test_row_count_matches_hours() -> None:
    df = parse_hourly_dataframe(_make_hourly_mock(N_HOURS), UTC_OFFSET)
    assert len(df) == N_HOURS


def test_date_column_hourly_is_timezone_aware() -> None:
    df = parse_hourly_dataframe(_make_hourly_mock(), UTC_OFFSET)
    assert df["date"].dt.tz is not None


def test_no_null_hourly_values() -> None:
    df = parse_hourly_dataframe(_make_hourly_mock(), UTC_OFFSET)
    assert not df.isnull().any().any()


def test_date_interval_is_one_hour() -> None:
    df = parse_hourly_dataframe(_make_hourly_mock(), UTC_OFFSET)
    diffs = df["date"].diff().dropna().unique()
    assert len(diffs) == 1
    assert diffs[0] == pd.Timedelta(hours=1)


def test_returns_daily_dataframe() -> None:
    df = parse_daily_dataframe(_make_daily_mock(), UTC_OFFSET)
    assert isinstance(df, pd.DataFrame)


def test_has_correct_daily_columns() -> None:
    df = parse_daily_dataframe(_make_daily_mock(), UTC_OFFSET)
    assert list(df.columns) == DAILY_COLUMNS


def test_row_count_matches_days() -> None:
    df = parse_daily_dataframe(_make_daily_mock(N_DAYS), UTC_OFFSET)
    assert len(df) == N_DAYS


def test_date_column_daily_is_timezone_aware() -> None:
    df = parse_daily_dataframe(_make_daily_mock(), UTC_OFFSET)
    assert df["date"].dt.tz is not None


def test_no_null_daily_values() -> None:
    df = parse_daily_dataframe(_make_daily_mock(), UTC_OFFSET)
    assert not df.isnull().any().any()


def test_date_interval_is_one_day() -> None:
    df = parse_daily_dataframe(_make_daily_mock(), UTC_OFFSET)
    diffs = df["date"].diff().dropna().unique()
    assert len(diffs) == 1
    assert diffs[0] == pd.Timedelta(days=1)


def test_sunrise_sunset_are_integer() -> None:
    df = parse_daily_dataframe(_make_daily_mock(), UTC_OFFSET)
    assert pd.api.types.is_integer_dtype(df["sunrise"])
    assert pd.api.types.is_integer_dtype(df["sunset"])


def test_returns_first_element() -> None:
    sentinel = object()
    mock_client = MagicMock()
    mock_client.weather_api.return_value = [sentinel]
    result = fetch_weather_response(mock_client, {})
    assert result is sentinel


def test_passes_parameters_to_api() -> None:
    mock_client = MagicMock()
    mock_client.weather_api.return_value = [MagicMock()]
    parameters = {"foo": "bar"}
    fetch_weather_response(mock_client, parameters)
    mock_client.weather_api.assert_called_once()
    _, call_kwargs = mock_client.weather_api.call_args

    call_args_pos = mock_client.weather_api.call_args[0]
    assert parameters in call_args_pos or call_kwargs.get("parameters") == parameters


def _make_response_mock() -> MagicMock:
    response = MagicMock()
    response.UtcOffsetSeconds.return_value = UTC_OFFSET
    response.Hourly.return_value = _make_hourly_mock()
    response.Daily.return_value = _make_daily_mock()
    return response


@patch("src.app.openmeteo.gather.build_openmeteo_client")
@patch("src.app.openmeteo.fetch.fetch_weather_response")
def test_returns_two_dataframes(mock_fetch: MagicMock, mock_client: MagicMock) -> None:
    mock_fetch.return_value = _make_response_mock()
    hourly_df, daily_df = gather_data()
    assert isinstance(hourly_df, pd.DataFrame)
    assert isinstance(daily_df, pd.DataFrame)


@patch("src.app.openmeteo.gather.build_openmeteo_client")
@patch("src.app.openmeteo.fetch.fetch_weather_response")
def test_hourly_has_expected_columns(mock_fetch: MagicMock, mock_client: MagicMock) -> None:
    mock_fetch.return_value = _make_response_mock()
    hourly_df, _ = gather_data()
    for col in HOURLY_COLUMNS:
        assert col in hourly_df.columns


@patch("src.app.openmeteo.gather.build_openmeteo_client")
@patch("src.app.openmeteo.fetch.fetch_weather_response")
def test_daily_has_expected_columns(mock_fetch: MagicMock, mock_client: MagicMock) -> None:
    mock_fetch.return_value = _make_response_mock()
    _, daily_df = gather_data()
    for col in DAILY_COLUMNS:
        assert col in daily_df.columns


@patch("src.app.openmeteo.gather.build_openmeteo_client")
@patch("src.app.openmeteo.fetch.fetch_weather_response")
def test_uses_utc_offset_from_response(mock_fetch: MagicMock, mock_client: MagicMock) -> None:
    response = _make_response_mock()
    mock_fetch.return_value = response
    gather_data()
    response.UtcOffsetSeconds.assert_called_once()
