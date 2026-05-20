from abc import ABC, abstractmethod
from datetime import datetime

import httpx
import structlog

from src.api.time_provider.http_time_provider import AisenseApiProvider, GettimeApiProvider

logger = structlog.get_logger(__name__)


class TimeProvider(ABC):
    @abstractmethod
    async def fetch_time(self) -> datetime | None:
        pass



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
