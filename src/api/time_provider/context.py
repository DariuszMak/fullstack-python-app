from datetime import datetime

import structlog

from src.api.time_provider.http_time_provider import HttpTimeProvider
from src.api.time_provider.time_provider import TimeProvider
from src.api.time_provider.time_sync_context import TimeSyncContext

logger = structlog.get_logger(__name__)


class GetTimeApiProvider(HttpTimeProvider):
    def __init__(self) -> None:
        super().__init__(
            url="https://gettimeapi.dev/v1/time?timezone=UTC",
            datetime_key="iso8601",
        )


class AiSenseApiProvider(HttpTimeProvider):
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


def default_time_sync_context() -> TimeSyncContext:
    return TimeSyncContext(
        providers=[
            GetTimeApiProvider(),
            AiSenseApiProvider(),
            LocalTimeProvider(),
        ]
    )
