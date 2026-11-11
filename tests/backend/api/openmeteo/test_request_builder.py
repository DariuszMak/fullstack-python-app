from typing import Any

import pytest

import src.backend.openmeteo.places.places as places_module
from src.backend.openmeteo.request_builder import (
    API_URL,
    DAILY_VARIABLES,
    HOURLY_VARIABLES,
    MAX_FORECAST_DAYS,
    build_request_parameters,
)


@pytest.fixture(autouse=True)
def mock_places_constants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(places_module, "LATITUDE", 52.2297)
    monkeypatch.setattr(places_module, "LONGITUDE", 21.0122)
    monkeypatch.setattr(places_module, "TIMEZONE", "Europe/Warsaw")


def test_constants() -> None:
    assert MAX_FORECAST_DAYS == 16
    assert API_URL == "https://api.open-meteo.com/v1/forecast"
    assert len(DAILY_VARIABLES) > 0
    assert len(HOURLY_VARIABLES) > 0


def test_build_request_parameters_defaults() -> None:
    params: dict[str, Any] = build_request_parameters()

    assert params["latitude"] == pytest.approx(51.9727)
    assert params["longitude"] == pytest.approx(17.5026)
    assert params["timezone"] == "Europe/Berlin"
    assert params["forecast_days"] == 16
    assert params["daily"] == DAILY_VARIABLES
    assert params["hourly"] == HOURLY_VARIABLES


@pytest.mark.parametrize(
    ("latitude", "longitude", "timezone", "forecast_days", "include_hourly", "include_daily"),
    [
        (10.5, 20.2, "UTC", 5, True, True),
        (-33.8, 151.2, "Australia/Sydney", 10, False, True),
        (0.0, 0.0, "GMT", 3, True, False),
        (45.1, -93.2, "America/Chicago", 16, False, False),
    ],
)
def test_build_request_parameters_custom(
    latitude: float,
    longitude: float,
    timezone: str,
    forecast_days: int,
    include_hourly: bool,
    include_daily: bool,
) -> None:
    params: dict[str, Any] = build_request_parameters(
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        forecast_days=forecast_days,
        include_hourly=include_hourly,
        include_daily=include_daily,
    )

    assert params["latitude"] == latitude
    assert params["longitude"] == longitude
    assert params["timezone"] == timezone
    assert params["forecast_days"] == forecast_days

    if include_daily:
        assert params["daily"] == DAILY_VARIABLES
    else:
        assert "daily" not in params

    if include_hourly:
        assert params["hourly"] == HOURLY_VARIABLES
    else:
        assert "hourly" not in params
