LATITUDE: float = 51.9727
LONGITUDE: float = 17.5026
TIMEZONE: str = "Europe/Berlin"
FORECAST_DAYS: int = 16
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


def build_request_params(
    latitude: float = LATITUDE,
    longitude: float = LONGITUDE,
    timezone: str = TIMEZONE,
    forecast_days: int = FORECAST_DAYS,
) -> dict[str, object]:
    return {
        "latitude": latitude,
        "longitude": longitude,
        "daily": DAILY_VARIABLES,
        "hourly": HOURLY_VARIABLES,
        "timezone": timezone,
        "forecast_days": forecast_days,
    }
