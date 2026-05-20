from abc import ABC, abstractmethod
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


class TimeProvider(ABC):
    @abstractmethod
    async def fetch_time(self) -> datetime | None:
        pass
