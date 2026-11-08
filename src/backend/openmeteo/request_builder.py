from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.backend.openmeteo.places.places import LATITUDE, LONGITUDE, TIMEZONE

MAX_FORECAST_DAYS: int = 16
API_URL: str = "https://api.open-meteo.com/v1/forecast"

DAILY_VARIABLES: list[str] = [
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

HOURLY_VARIABLES: list[str] = [
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


def build_request_parameters(
    latitude: float = LATITUDE,
    longitude: float = LONGITUDE,
    timezone: str = TIMEZONE,
    forecast_days: int = MAX_FORECAST_DAYS,
    start_day: int = 0,
    include_hourly: bool = True,
    include_daily: bool = True,
    today: date | None = None,
) -> dict[str, object]:
    params: dict[str, object] = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
    }

    if start_day > 0:
        start_date, end_date = _date_window(start_day, forecast_days, timezone, today)
        params["start_date"] = start_date.isoformat()
        params["end_date"] = end_date.isoformat()
    else:
        params["forecast_days"] = forecast_days

    if include_daily:
        params["daily"] = DAILY_VARIABLES
    if include_hourly:
        params["hourly"] = HOURLY_VARIABLES

    return params


def _date_window(
    start_day: int,
    forecast_days: int,
    timezone: str,
    today: date | None,
) -> tuple[date, date]:
    base = today if today is not None else _today_in(timezone)
    last_allowed = base + timedelta(days=MAX_FORECAST_DAYS - 1)
    start = min(base + timedelta(days=start_day), last_allowed)
    end = min(start + timedelta(days=max(forecast_days, 1) - 1), last_allowed)
    return start, end


def _today_in(timezone: str) -> date:
    try:
        tz = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()
