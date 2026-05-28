from dataclasses import dataclass
from pathlib import Path

import structlog
from fastapi import APIRouter, Response
from fastapi.responses import FileResponse

from src.backend.api.models.best_score_response import BestScoreQueryParams, BestScoreResponse
from src.backend.api.models.helpers.best_score_calculator import calculate_best_scores
from src.backend.api.models.helpers.weather_info_parse import parse_weather_records
from src.backend.api.models.weather_info_response import (
    WeatherInfoResponse,
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


@router.get("/api/v1/ping")
async def ping() -> dict[str, str]:
    return {"message": "pong"}


@router.get("/api/v1/time")
async def current_time() -> dict[str, str]:
    dt = await time_sync_context_container.context.get_current_time()
    return {"datetime": dt.isoformat()}


@router.post("/api/v1/forecast/info")
def info_weather(params: WeatherQueryParams) -> WeatherInfoResponse:
    parameters = build_request_parameters(
        latitude=params.latitude,
        longitude=params.longitude,
        timezone=params.timezone,
        forecast_days=params.forecast_days,
    )

    hourly_df, daily_df = gather_data(parameters)

    hourly_records, daily_records = parse_weather_records(hourly_df, daily_df)

    result = WeatherInfoResponse(
        hourly=hourly_records,
        daily=daily_records,
        hourly_rows=len(hourly_records),
        daily_rows=len(daily_records),
    )

    return result


@router.post("/api/v1/forecast/weather-score")
async def weather_score(params: BestScoreQueryParams) -> BestScoreResponse:
    results = await calculate_best_scores(params)

    return BestScoreResponse(
        results=results,
        threshold=params.apparent_temperature_threshold,
        penalize_rain=params.penalize_rain,
        start_day=params.start_day,
    )


@router.get("/{full_path:path}", include_in_schema=False)
async def ignore_noise(full_path: str) -> Response:
    if full_path.startswith(".well-known") or full_path.endswith(".map"):
        return Response(status_code=204)

    logger.debug("unhandled_path_requested", path=full_path)
    return Response(status_code=404)
