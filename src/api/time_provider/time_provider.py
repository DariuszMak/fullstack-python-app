from abc import ABC, abstractmethod
from datetime import datetime

import structlog

from src.api.time_provider.aisense_api_provider import AisenseApiProvider
from src.api.time_provider.gettime_api_provider import GettimeApiProvider
from src.api.time_provider.local_time_provider import LocalTimeProvider
from src.api.time_provider.time_sync_context import TimeSyncContext

logger = structlog.get_logger(__name__)


class TimeProvider(ABC):
    @abstractmethod
    async def fetch_time(self) -> datetime | None:
        pass


def default_time_sync_context() -> TimeSyncContext:
    return TimeSyncContext(
        providers=[
            GettimeApiProvider(),
            AisenseApiProvider(),
            LocalTimeProvider(),
        ]
    )
