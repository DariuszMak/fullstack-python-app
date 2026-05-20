from abc import ABC, abstractmethod
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger(__name__)


class TimeProvider(ABC):
    @abstractmethod
    async def fetch_time(self) -> datetime | None:
        pass


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


class GettimeApiProvider(HttpTimeProvider):
    def __init__(self) -> None:
        super().__init__(
            url="https://gettimeapi.dev/v1/time?timezone=UTC",
            datetime_key="iso8601",
        )


class AisenseApiProvider(HttpTimeProvider):
    def __init__(self) -> None:
        super().__init__(
            url="https://aisenseapi.com/services/v1/datetime",
            datetime_key="datetime",
        )


class LocalTimeProvider(TimeProvider):
    async def fetch_time(self) -> datetime:
        dt = datetime.now().astimezone()
        logger.info("falling_back_to_local_time", timestamp=dt.isoformat())
        return dt


class TimeSyncContext:
    def __init__(self, providers: list[TimeProvider]) -> None:
        if not providers:
            raise ValueError("At least one TimeProvider is required.")
        self._providers = providers

    async def get_current_time(self) -> datetime:
        for provider in self._providers:
            result = await provider.fetch_time()
            if result is not None:
                return result

        raise RuntimeError("All time providers failed and no fallback was available.")


def default_time_sync_context() -> TimeSyncContext:
    return TimeSyncContext(
        providers=[
            GettimeApiProvider(),
            AisenseApiProvider(),
            LocalTimeProvider(),
        ]
    )
