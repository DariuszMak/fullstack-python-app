from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.backend.api.app import app
from src.backend.api.models.best_score_response import BestScoreQueryParams, PlaceBestScoreRecord
from src.backend.api.models.helpers.best_score_calculator import _day_weight, _score_place, calculate_best_scores

N_DAYS = 4


def _make_daily_df(
    n: int = N_DAYS,
    apparent_max: float = 25.0,
    rain_sum: float = 0.0,
) -> pd.DataFrame:
    dates = pd.date_range(start=pd.Timestamp("2026-05-22", tz="UTC"), periods=n, freq="D")
    return pd.DataFrame({
        "date": dates,
        "sunshine_duration": np.full(n, 40000.0, dtype=np.float32),
        "uv_index_max": np.full(n, 5.0, dtype=np.float32),
        "apparent_temperature_max": np.full(n, apparent_max, dtype=np.float32),
        "apparent_temperature_min": np.full(n, 10.0, dtype=np.float32),
        "sunrise": np.array([1779417972 + i * 86400 for i in range(n)], dtype=np.int64),
        "sunset": np.array([1779475626 + i * 86400 for i in range(n)], dtype=np.int64),
        "daylight_duration": np.full(n, 57000.0, dtype=np.float32),
        "rain_sum": np.full(n, rain_sum, dtype=np.float32),
        "temperature_2m_max": np.full(n, 26.0, dtype=np.float32),
        "temperature_2m_min": np.full(n, 11.0, dtype=np.float32),
    })


def test_day_weight_first_day_is_one() -> None:
    assert _day_weight(0, 10) == pytest.approx(1.0)


def test_day_weight_last_day_is_near_zero() -> None:
    assert _day_weight(9, 10) == pytest.approx(0.1)


def test_day_weight_middle_day() -> None:
    assert _day_weight(5, 10) == pytest.approx(0.5)


def test_score_place_zero_when_all_below_threshold() -> None:
    df = _make_daily_df(apparent_max=15.0)
    score = _score_place(df, threshold=20.0, penalize_rain=False)
    assert score == pytest.approx(0.0)


def test_score_place_positive_when_above_threshold() -> None:
    df = _make_daily_df(apparent_max=25.0)
    score = _score_place(df, threshold=20.0, penalize_rain=False)
    assert score > 0.0


def test_score_place_first_day_weighted_higher() -> None:
    n = 4
    dates = pd.date_range(start=pd.Timestamp("2026-05-22", tz="UTC"), periods=n, freq="D")
    apparent_values = [30.0, 20.1, 20.1, 20.1]
    df = pd.DataFrame({
        "date": dates,
        "sunshine_duration": np.full(n, 40000.0),
        "uv_index_max": np.full(n, 5.0),
        "apparent_temperature_max": apparent_values,
        "apparent_temperature_min": np.full(n, 10.0),
        "sunrise": np.array([1779417972 + i * 86400 for i in range(n)], dtype=np.int64),
        "sunset": np.array([1779475626 + i * 86400 for i in range(n)], dtype=np.int64),
        "daylight_duration": np.full(n, 57000.0),
        "rain_sum": np.zeros(n),
        "temperature_2m_max": np.full(n, 26.0),
        "temperature_2m_min": np.full(n, 11.0),
    })

    score_first_big = _score_place(df, threshold=20.0, penalize_rain=False)

    apparent_values_reversed = list(reversed(apparent_values))
    df2 = df.copy()
    df2["apparent_temperature_max"] = apparent_values_reversed
    score_last_big = _score_place(df2, threshold=20.0, penalize_rain=False)

    assert score_first_big > score_last_big


def test_score_place_rain_penalize_zeroes_rainy_days() -> None:
    n = 2
    dates = pd.date_range(start=pd.Timestamp("2026-05-22", tz="UTC"), periods=n, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "sunshine_duration": np.full(n, 40000.0),
        "uv_index_max": np.full(n, 5.0),
        "apparent_temperature_max": [25.0, 25.0],
        "apparent_temperature_min": np.full(n, 10.0),
        "sunrise": np.array([1779417972, 1779504372], dtype=np.int64),
        "sunset": np.array([1779475626, 1779562026], dtype=np.int64),
        "daylight_duration": np.full(n, 57000.0),
        "rain_sum": [5.0, 0.0],
        "temperature_2m_max": np.full(n, 26.0),
        "temperature_2m_min": np.full(n, 11.0),
    })

    score_no_penalize = _score_place(df, threshold=20.0, penalize_rain=False)
    score_penalize = _score_place(df, threshold=20.0, penalize_rain=True)

    assert score_penalize < score_no_penalize


def test_score_place_rain_penalize_false_keeps_rainy_days() -> None:
    df = _make_daily_df(apparent_max=25.0, rain_sum=10.0)
    score = _score_place(df, threshold=20.0, penalize_rain=False)
    assert score > 0.0


def test_score_place_all_rainy_penalized_is_zero() -> None:
    df = _make_daily_df(apparent_max=25.0, rain_sum=5.0)
    score = _score_place(df, threshold=20.0, penalize_rain=True)
    assert score == pytest.approx(0.0)


def test_score_place_exact_threshold_not_counted() -> None:
    df = _make_daily_df(apparent_max=20.0)
    score = _score_place(df, threshold=20.0, penalize_rain=False)
    assert score == pytest.approx(0.0)


@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
def test_calculate_best_scores_returns_all_places(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    from src.backend.openmeteo.places.places import PLACES

    mock_build.return_value = {}
    mock_gather.return_value = (pd.DataFrame(), _make_daily_df())

    params = BestScoreQueryParams()
    results = calculate_best_scores(params)

    assert len(results) == len(PLACES)


@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
def test_calculate_best_scores_sorted_descending(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    call_count = 0

    def side_effect(params: dict) -> tuple:
        nonlocal call_count
        apparent_max = 20.0 + call_count * 1.0
        call_count += 1
        return pd.DataFrame(), _make_daily_df(apparent_max=apparent_max)

    mock_gather.side_effect = side_effect

    params = BestScoreQueryParams(apparent_temperature_threshold=15.0)
    results = calculate_best_scores(params)

    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
def test_calculate_best_scores_record_has_all_fields(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (pd.DataFrame(), _make_daily_df())

    params = BestScoreQueryParams()
    results = calculate_best_scores(params)

    for record in results:
        assert isinstance(record, PlaceBestScoreRecord)
        assert record.key
        assert record.name
        assert isinstance(record.latitude, float)
        assert isinstance(record.longitude, float)
        assert record.timezone
        assert isinstance(record.score, float)


@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
def test_calculate_best_scores_passes_forecast_days(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (pd.DataFrame(), _make_daily_df())

    params = BestScoreQueryParams(forecast_days=7)
    calculate_best_scores(params)

    for call in mock_build.call_args_list:
        assert call.kwargs.get("forecast_days") == 7


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_returns_200(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        response = client.post("/api/v1/weather/best_score", json={})

    assert response.status_code == 200


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_response_has_required_keys(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/best_score", json={}).json()

    assert "results" in data
    assert "threshold" in data
    assert "penalize_rain" in data


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_reflects_threshold(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/best_score", json={"apparent_temperature_threshold": 18.5}).json()

    assert data["threshold"] == pytest.approx(18.5)


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_reflects_penalize_rain(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/best_score", json={"penalize_rain": True}).json()

    assert data["penalize_rain"] is True


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_rejects_forecast_days_out_of_range(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        r1 = client.post("/api/v1/weather/best_score", json={"forecast_days": 0})
        r2 = client.post("/api/v1/weather/best_score", json={"forecast_days": 17})

    assert r1.status_code == 422
    assert r2.status_code == 422


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_passes_params_to_calculator(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    payload = {
        "apparent_temperature_threshold": 22.0,
        "penalize_rain": True,
        "forecast_days": 5,
    }

    with TestClient(app) as client:
        client.post("/api/v1/weather/best_score", json=payload)

    mock_calc.assert_called_once()
    called_params: BestScoreQueryParams = mock_calc.call_args[0][0]
    assert called_params.apparent_temperature_threshold == pytest.approx(22.0)
    assert called_params.penalize_rain is True
    assert called_params.forecast_days == 5


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_result_fields(mock_calc: MagicMock) -> None:
    mock_calc.return_value = [
        PlaceBestScoreRecord(
            key="jarocin",
            name="Jarocin",
            latitude=51.9727,
            longitude=17.5026,
            timezone="Europe/Berlin",
            score=42.5,
        )
    ]

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/best_score", json={}).json()

    record = data["results"][0]
    assert record["key"] == "jarocin"
    assert record["name"] == "Jarocin"
    assert record["score"] == pytest.approx(42.5)
