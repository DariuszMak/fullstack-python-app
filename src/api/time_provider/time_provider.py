from abc import ABC, abstractmethod
from datetime import datetime

from src.api.time_provider.AisenseApiProvider import AisenseApiProvider
from src.api.time_provider.GettimeApiProvider import GettimeApiProvider
from src.api.time_provider.LocalTimeProvider import LocalTimeProvider
import structlog

from src.api.time_provider.TimeSyncContext import TimeSyncContext

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
