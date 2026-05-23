import math
from dataclasses import dataclass
from pathlib import Path

import structlog
from fastapi import APIRouter, Response
from fastapi.responses import FileResponse

from src.backend.api.models.weather_info_response import (
    DailyRecord,
    HourlyRecord,
    WeatherCalculationResponse,
    WeatherQueryParams,
)
from src.backend.api.time_provider.context import default_time_sync_context
from src.backend.api.time_provider.time_sync_context import TimeSyncContext
from src.backend.openmeteo.gather import gather_data
from src.backend.openmeteo.request_builder import build_request_parameters

logger = structlog.get_logger(__name__)
router = APIRouter()


@dataclass
class TimeSyncContextContainer:
    context: TimeSyncContext


time_sync_context_container = TimeSyncContextContainer(context=default_time_sync_context())


def set_time_sync_context(context: TimeSyncContext) -> None:
    time_sync_context_container.context = context


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(Path("src/ui/pyside_ui/forms/icons/images/program_icon.ico"))


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"message": "pong"}


@router.get("/time")
async def current_time() -> dict[str, str]:
    dt = await time_sync_context_container.context.get_current_time()
    return {"datetime": dt.isoformat()}


def _sanitize_float(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(value)


@router.post("/api/v1/weather/info", response_model=WeatherCalculationResponse)
def info_weather(params: WeatherQueryParams) -> WeatherCalculationResponse:
    parameters = build_request_parameters(
        latitude=params.latitude,
        longitude=params.longitude,
        timezone=params.timezone,
        forecast_days=params.forecast_days,
    )

    hourly_df, daily_df = gather_data(parameters)

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

    result = WeatherCalculationResponse(
        hourly=hourly_records,
        daily=daily_records,
        hourly_rows=len(hourly_records),
        daily_rows=len(daily_records),
    )

    return result


@router.get("/{full_path:path}", include_in_schema=False)
async def ignore_noise(full_path: str) -> Response:
    if full_path.startswith(".well-known") or full_path.endswith(".map"):
        return Response(status_code=204)

    logger.debug("unhandled_path_requested", path=full_path)
    return Response(status_code=404)
