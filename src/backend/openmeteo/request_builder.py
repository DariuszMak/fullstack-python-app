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
    include_hourly: bool = True,
    include_daily: bool = True,
) -> dict[str, object]:
    params: dict[str, object] = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "forecast_days": forecast_days,
    }

    if include_daily:
        params["daily"] = DAILY_VARIABLES
    if include_hourly:
        params["hourly"] = HOURLY_VARIABLES

    return params
