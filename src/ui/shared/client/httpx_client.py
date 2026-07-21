from __future__ import annotations

from datetime import datetime

import httpx
import structlog

from src.backend.api.models.server_time_response import ServerTimeResponse
from src.backend.api.models.weather_score_response import BestScoreResponse

logger = structlog.get_logger(__name__)


class HttpxClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(5.0, connect=3.0, read=10.0)

    async def fetch_time(self) -> ServerTimeResponse:
        url = f"{self._base_url}/api/v1/time"
        log = logger.bind(url=url)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError as e:
                log.exception("server_time_fetch_failed", error=str(e))
                raise

        payload = response.json()
        server_time = datetime.fromisoformat(payload["datetime"])

        log.debug("server_time_fetched", server_time=server_time.isoformat())

        return ServerTimeResponse(datetime=server_time)

    async def fetch_weather_score(
        self,
        apparent_temperature_min_threshold: float | None = None,
        apparent_temperature_max_threshold: float | None = None,
        penalize_rain: bool | None = None,
        forecast_days: int | None = None,
        start_day: int | None = None,
    ) -> BestScoreResponse:
        url = f"{self._base_url}/api/v1/forecast/weather-score"
        log = logger.bind(url=url)

        body: dict[str, float | bool | int] = {}

        if apparent_temperature_min_threshold is not None:
            body["apparent_temperature_min_threshold"] = apparent_temperature_min_threshold
        if apparent_temperature_max_threshold is not None:
            body["apparent_temperature_max_threshold"] = apparent_temperature_max_threshold
        if penalize_rain is not None:
            body["penalize_rain"] = penalize_rain
        if forecast_days is not None:
            body["forecast_days"] = forecast_days
        if start_day is not None:
            body["start_day"] = start_day

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=body)
                response.raise_for_status()
            except httpx.HTTPError as e:
                log.exception("weather_score_fetch_failed", error=str(e))
                raise

        payload = response.json()

        log.debug("weather_score_fetched", result_count=len(payload.get("results", [])))

        return BestScoreResponse.model_validate(payload)
