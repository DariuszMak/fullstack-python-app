from dataclasses import dataclass
from pathlib import Path

import structlog
from fastapi import APIRouter, Response
from fastapi.responses import FileResponse

from src.backend.api.models.weather_calculation_response import WeatherQueryParams
from src.backend.api.time_provider.context import default_time_sync_context
from src.backend.api.time_provider.time_sync_context import TimeSyncContext

logger = structlog.get_logger(__name__)
router = APIRouter()


@dataclass
class TimeSyncContextContainer:
    context: TimeSyncContext


time_sync_context_container = TimeSyncContextContainer(context=default_time_sync_context())


def set_time_sync_context(context: TimeSyncContext) -> None:
    time_sync_context_container.context = context


@router.get("/{full_path:path}", include_in_schema=False)
async def ignore_noise(full_path: str) -> Response:
    if full_path.startswith(".well-known") or full_path.endswith(".map"):
        return Response(status_code=204)

    logger.debug("unhandled_path_requested", path=full_path)
    return Response(status_code=404)


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


@router.post("/api/v1/weather/calculate")
def calculate_weather(params: WeatherQueryParams):
    result = {
        "temperature": params.Temperature
    }
    return result