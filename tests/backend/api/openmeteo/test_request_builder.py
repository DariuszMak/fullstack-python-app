from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from src.backend.openmeteo import request_builder
from src.backend.openmeteo.places.places import LATITUDE, LONGITUDE, TIMEZONE
from src.backend.openmeteo.request_builder import (
    API_URL,
    DAILY_VARIABLES,
    HOURLY_VARIABLES,
    MAX_FORECAST_DAYS,
    build_request_parameters,
)

TODAY = date(2026, 11, 6)


def test_api_url() -> None:
    assert API_URL == "https://api.open-meteo.com/v1/forecast"


def test_defaults_use_place_constants_and_max_forecast_days() -> None:
    params = build_request_parameters()

    assert params["latitude"] == LATITUDE
    assert params["longitude"] == LONGITUDE
    assert params["timezone"] == TIMEZONE
    assert params["forecast_days"] == MAX_FORECAST_DAYS


def test_default_includes_daily_and_hourly_variables() -> None:
    params = build_request_parameters()

    assert params["daily"] == DAILY_VARIABLES
    assert params["hourly"] == HOURLY_VARIABLES


def test_hourly_variables_contain_precipitation() -> None:
    assert "precipitation" in HOURLY_VARIABLES


def test_exclude_hourly() -> None:
    params = build_request_parameters(include_hourly=False)

    assert "hourly" not in params
    assert "daily" in params


def test_exclude_daily() -> None:
    params = build_request_parameters(include_daily=False)

    assert "daily" not in params
    assert "hourly" in params


def test_custom_location_and_forecast_days() -> None:
    params = build_request_parameters(latitude=50.0, longitude=15.0, timezone="Europe/Warsaw", forecast_days=5)

    assert params["latitude"] == pytest.approx(50.0)
    assert params["longitude"] == pytest.approx(15.0)
    assert params["timezone"] == "Europe/Warsaw"
    assert params["forecast_days"] == 5


def test_start_day_zero_uses_forecast_days_only() -> None:
    params = build_request_parameters(forecast_days=3, start_day=0, today=TODAY)

    assert params["forecast_days"] == 3
    assert "start_date" not in params
    assert "end_date" not in params


def test_start_day_positive_sends_start_and_end_date_without_forecast_days() -> None:
    params = build_request_parameters(forecast_days=3, start_day=2, today=TODAY)

    assert params["start_date"] == "2026-11-08"
    assert params["end_date"] == "2026-11-10"
    assert "forecast_days" not in params


def test_start_day_one_is_tomorrow() -> None:
    params = build_request_parameters(forecast_days=3, start_day=1, today=TODAY)

    assert params["start_date"] == "2026-11-07"
    assert params["end_date"] == "2026-11-09"


def test_single_day_window_has_equal_start_and_end() -> None:
    params = build_request_parameters(forecast_days=1, start_day=3, today=TODAY)

    assert params["start_date"] == params["end_date"] == "2026-11-09"


def test_end_date_is_clamped_to_forecast_horizon() -> None:
    params = build_request_parameters(forecast_days=5, start_day=14, today=TODAY)

    assert params["start_date"] == "2026-11-20"
    assert params["end_date"] == "2026-11-21"


def test_start_date_is_clamped_to_forecast_horizon() -> None:
    params = build_request_parameters(forecast_days=5, start_day=50, today=TODAY)

    assert params["start_date"] == "2026-11-21"
    assert params["end_date"] == "2026-11-21"


def test_forecast_days_below_one_still_yields_single_day() -> None:
    params = build_request_parameters(forecast_days=0, start_day=1, today=TODAY)

    assert params["start_date"] == params["end_date"] == "2026-11-07"


def test_start_and_end_date_are_both_present_together() -> None:
    params = build_request_parameters(forecast_days=4, start_day=6, today=TODAY)

    assert ("start_date" in params) == ("end_date" in params)


def test_today_defaults_to_timezone_aware_today() -> None:
    with patch.object(request_builder, "_today_in", return_value=TODAY) as today_in:
        params = build_request_parameters(forecast_days=2, start_day=1, timezone="Europe/Warsaw")

    today_in.assert_called_once_with("Europe/Warsaw")
    assert params["start_date"] == "2026-11-07"
    assert params["end_date"] == "2026-11-08"


def test_explicit_today_skips_timezone_lookup() -> None:
    with patch.object(request_builder, "_today_in") as today_in:
        build_request_parameters(forecast_days=2, start_day=1, today=TODAY)

    today_in.assert_not_called()


def test_today_in_returns_date_for_valid_timezone() -> None:
    assert isinstance(request_builder._today_in("Europe/Warsaw"), date)


@pytest.mark.parametrize("timezone", ["Not/AZone", "", "../etc"])
def test_today_in_falls_back_to_utc_for_invalid_timezone(timezone: str) -> None:
    assert isinstance(request_builder._today_in(timezone), date)
