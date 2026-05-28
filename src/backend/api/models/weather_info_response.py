from __future__ import annotations

from pydantic import BaseModel


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
