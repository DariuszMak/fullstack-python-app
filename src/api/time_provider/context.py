import structlog

from src.api.time_provider.strategy.ai_sense_api_provider import AiSenseApiProvider
from src.api.time_provider.strategy.get_time_api_provider import GetTimeApiProvider
from src.api.time_provider.strategy.local_time_provider import LocalTimeProvider
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
