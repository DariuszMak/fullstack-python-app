from __future__ import annotations

from datetime import datetime

import httpx
import structlog

from src.api.models import ServerTimeResponse

logger = structlog.get_logger(__name__)


class TimeClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def fetch_time(self) -> ServerTimeResponse:
        url = f"{self._base_url}/time"
        log = logger.bind(url=url)

        async with httpx.AsyncClient() as client:
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
