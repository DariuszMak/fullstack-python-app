from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

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


# ---------------------------------------------------------------------------
# _day_weight
# ---------------------------------------------------------------------------


def test_day_weight_first_day_is_one() -> None:
    assert _day_weight(0, 10) == pytest.approx(1.0)


def test_day_weight_last_day_is_near_zero() -> None:
    assert _day_weight(9, 10) == pytest.approx(0.1)


def test_day_weight_middle_day() -> None:
    assert _day_weight(5, 10) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# _score_place
# ---------------------------------------------------------------------------


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

    df2 = df.copy()
    df2["apparent_temperature_max"] = list(reversed(apparent_values))
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


# ---------------------------------------------------------------------------
# BestScoreQueryParams — day range validation
# ---------------------------------------------------------------------------


def test_params_end_day_defaults_to_forecast_days() -> None:
    params = BestScoreQueryParams(forecast_days=10)
    assert params.end_day == 10


def test_params_explicit_start_end_accepted() -> None:
    params = BestScoreQueryParams(forecast_days=16, start_day=3, end_day=7)
    assert params.start_day == 3
    assert params.end_day == 7


def test_params_end_day_exceeds_forecast_days_raises() -> None:
    with pytest.raises(ValueError, match="end_day"):
        BestScoreQueryParams(forecast_days=5, end_day=6)


def test_params_start_day_gte_end_day_raises() -> None:
    with pytest.raises(ValueError, match="start_day"):
        BestScoreQueryParams(forecast_days=10, start_day=5, end_day=5)


def test_params_start_day_gt_end_day_raises() -> None:
    with pytest.raises(ValueError, match="start_day"):
        BestScoreQueryParams(forecast_days=10, start_day=7, end_day=3)


# ---------------------------------------------------------------------------
# calculate_best_scores (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
async def test_calculate_best_scores_returns_all_places(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    from src.backend.openmeteo.places.places import PLACES

    mock_build.return_value = {}
    mock_gather.return_value = (pd.DataFrame(), _make_daily_df())

    params = BestScoreQueryParams()
    results = await calculate_best_scores(params)

    assert len(results) == len(PLACES)


@pytest.mark.asyncio
@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
async def test_calculate_best_scores_sorted_descending(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    call_count = 0

    def side_effect(params: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
        nonlocal call_count
        apparent_max = 20.0 + call_count * 1.0
        call_count += 1
        return pd.DataFrame(), _make_daily_df(apparent_max=apparent_max)

    mock_gather.side_effect = side_effect

    params = BestScoreQueryParams(apparent_temperature_threshold=15.0)
    results = await calculate_best_scores(params)

    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
async def test_calculate_best_scores_record_has_all_fields(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (pd.DataFrame(), _make_daily_df())

    params = BestScoreQueryParams()
    results = await calculate_best_scores(params)

    for record in results:
        assert isinstance(record, PlaceBestScoreRecord)
        assert record.key
        assert record.name
        assert isinstance(record.latitude, float)
        assert isinstance(record.longitude, float)
        assert record.timezone
        assert isinstance(record.score, float)


@pytest.mark.asyncio
@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
async def test_calculate_best_scores_passes_forecast_days(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    mock_build.return_value = {}
    mock_gather.return_value = (pd.DataFrame(), _make_daily_df())

    params = BestScoreQueryParams(forecast_days=7)
    await calculate_best_scores(params)

    for call in mock_build.call_args_list:
        assert call.kwargs.get("forecast_days") == 7


@pytest.mark.asyncio
@patch("src.backend.api.models.helpers.best_score_calculator.gather_data")
@patch("src.backend.api.models.helpers.best_score_calculator.build_request_parameters")
async def test_calculate_best_scores_only_scores_day_range(
    mock_build: MagicMock,
    mock_gather: MagicMock,
) -> None:
    """Scores computed with start_day=3, end_day=7 must use only those 4 rows."""
    mock_build.return_value = {}

    # Days 0-2: very hot (would dominate if included); days 3-6: just above threshold
    n = 10
    apparent_values = [40.0, 40.0, 40.0, 22.0, 22.0, 22.0, 22.0, 5.0, 5.0, 5.0]
    dates = pd.date_range(start=pd.Timestamp("2026-05-22", tz="UTC"), periods=n, freq="D")
    full_df = pd.DataFrame({
        "date": dates,
        "sunshine_duration": np.full(n, 40000.0, dtype=np.float32),
        "uv_index_max": np.full(n, 5.0, dtype=np.float32),
        "apparent_temperature_max": np.array(apparent_values, dtype=np.float32),
        "apparent_temperature_min": np.full(n, 10.0, dtype=np.float32),
        "sunrise": np.array([1779417972 + i * 86400 for i in range(n)], dtype=np.int64),
        "sunset": np.array([1779475626 + i * 86400 for i in range(n)], dtype=np.int64),
        "daylight_duration": np.full(n, 57000.0, dtype=np.float32),
        "rain_sum": np.zeros(n, dtype=np.float32),
        "temperature_2m_max": np.full(n, 26.0, dtype=np.float32),
        "temperature_2m_min": np.full(n, 11.0, dtype=np.float32),
    })

    mock_gather.return_value = (pd.DataFrame(), full_df)

    params_full = BestScoreQueryParams(
        forecast_days=10,
        apparent_temperature_threshold=20.0,
        penalize_rain=False,
    )
    results_full = await calculate_best_scores(params_full)
    scores_full = {r.key: r.score for r in results_full}

    params_range = BestScoreQueryParams(
        forecast_days=10,
        start_day=3,
        end_day=7,
        apparent_temperature_threshold=20.0,
        penalize_rain=False,
    )
    results_range = await calculate_best_scores(params_range)
    scores_range = {r.key: r.score for r in results_range}

    # Range scores must be lower since the hot early days are excluded
    for key in scores_full:
        assert scores_range[key] < scores_full[key], (
            f"Place {key}: range score {scores_range[key]} should be < full score {scores_full[key]}"
        )
