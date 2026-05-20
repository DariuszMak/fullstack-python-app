from datetime import datetime

import structlog

from src.api.time_provider.http_time_provider import HttpTimeProvider
from src.api.time_provider.time_provider import TimeProvider
from src.api.time_provider.time_sync_context import TimeSyncContext

logger = structlog.get_logger(__name__)



def default_time_sync_context() -> TimeSyncContext:
    return TimeSyncContext(
        providers=[
            GetTimeApiProvider(),
            AiSenseApiProvider(),
            LocalTimeProvider(),
        ]
    )
