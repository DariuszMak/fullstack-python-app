from __future__ import annotations

from pydantic import BaseModel, Field


class WeatherQueryParams(BaseModel):
    latitude: float = Field(default=51.9727, description="Latitude of the location")
    longitude: float = Field(default=17.5026, description="Longitude of the location")
    timezone: str = Field(default="Europe/Berlin", description="IANA timezone string")
    forecast_days: int = Field(default=3, ge=1, le=16, description="Number of forecast days (1-16)")


class HourlyRecord(BaseModel):
    date: str
    temperature_2m: float
    cloud_cover: float
    precipitation: float
    apparent_temperature: float
    soil_temperature_6cm: float
    relative_humidity_2m: float
    surface_pressure: float
    wind_speed_10m: float
    wind_direction_10m: float
    wind_gusts_10m: float
    soil_moisture_0_to_1cm: float


class DailyRecord(BaseModel):
    date: str
    sunshine_duration: float
    uv_index_max: float
    apparent_temperature_max: float
    apparent_temperature_min: float
    sunrise: int
    sunset: int
    daylight_duration: float
    rain_sum: float
    temperature_2m_max: float
    temperature_2m_min: float


class WeatherInfoResponse(BaseModel):
    hourly: list[HourlyRecord]
    daily: list[DailyRecord]
    hourly_rows: int
    daily_rows: int
