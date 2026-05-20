from datetime import datetime

import httpx

from .time_provider import TimeProvider, logger


class HttpTimeProvider(TimeProvider):
    def __init__(self, url: str, datetime_key: str) -> None:
        self._url = url
        self._datetime_key = datetime_key

    async def fetch_time(self) -> datetime | None:
        log = logger.bind(url=self._url)
        try:
            log.info("fetching_external_time")
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(self._url)
                resp.raise_for_status()

            data = resp.json()
            datetime_str = data.get(self._datetime_key)

            if datetime_str:
                dt = datetime.fromisoformat(datetime_str).astimezone()
                log.info("external_time_received", timestamp=dt.isoformat())
                return dt

        except httpx.HTTPError as e:
            log.warning("time_api_request_failed", error=str(e))

        return None