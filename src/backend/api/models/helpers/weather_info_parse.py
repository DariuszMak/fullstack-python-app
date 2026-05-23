import math

import pandas as pd
import structlog
from fastapi import APIRouter

from src.backend.api.models.weather_info_response import DailyRecord, HourlyRecord

logger = structlog.get_logger(__name__)
router = APIRouter()


def _sanitize_float(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(value)

def parse_weather_records(
    hourly_df: pd.DataFrame, daily_df: pd.DataFrame
) -> tuple[list[HourlyRecord], list[DailyRecord]]:
    hourly_records = [
        HourlyRecord(
            date=row["date"].isoformat(),
            temperature_2m=_sanitize_float(row["temperature_2m"]),
            cloud_cover=_sanitize_float(row["cloud_cover"]),
            precipitation=_sanitize_float(row["precipitation"]),
            apparent_temperature=_sanitize_float(row["apparent_temperature"]),
            soil_temperature_6cm=_sanitize_float(row["soil_temperature_6cm"]),
            relative_humidity_2m=_sanitize_float(row["relative_humidity_2m"]),
            surface_pressure=_sanitize_float(row["surface_pressure"]),
            wind_speed_10m=_sanitize_float(row["wind_speed_10m"]),
            wind_direction_10m=_sanitize_float(row["wind_direction_10m"]),
            wind_gusts_10m=_sanitize_float(row["wind_gusts_10m"]),
            soil_moisture_0_to_1cm=_sanitize_float(row["soil_moisture_0_to_1cm"]),
        )
        for row in hourly_df.to_dict(orient="records")
    ]

    daily_records = [
        DailyRecord(
            date=row["date"].isoformat(),
            sunshine_duration=_sanitize_float(row["sunshine_duration"]),
            uv_index_max=_sanitize_float(row["uv_index_max"]),
            apparent_temperature_max=_sanitize_float(row["apparent_temperature_max"]),
            apparent_temperature_min=_sanitize_float(row["apparent_temperature_min"]),
            sunrise=int(row["sunrise"]),
            sunset=int(row["sunset"]),
            daylight_duration=_sanitize_float(row["daylight_duration"]),
            rain_sum=_sanitize_float(row["rain_sum"]),
            temperature_2m_max=_sanitize_float(row["temperature_2m_max"]),
            temperature_2m_min=_sanitize_float(row["temperature_2m_min"]),
        )
        for row in daily_df.to_dict(orient="records")
    ]

    return hourly_records, daily_records
