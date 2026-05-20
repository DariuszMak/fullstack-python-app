from abc import ABC, abstractmethod
from datetime import datetime

import structlog

from .AisenseApiProvider import AisenseApiProvider
from .GettimeApiProvider import GettimeApiProvider
from .LocalTimeProvider import LocalTimeProvider
from .TimeSyncContext import TimeSyncContext

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