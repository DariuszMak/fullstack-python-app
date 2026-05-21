import structlog

from src.backend.api.time_provider.strategy.ai_sense_api import AiSenseApi
from src.backend.api.time_provider.strategy.get_time_api import GetTimeApi
from src.backend.api.time_provider.strategy.local_time import LocalTime
from src.backend.api.time_provider.time_sync_context import TimeSyncContext

logger = structlog.get_logger(__name__)


def default_time_sync_context() -> TimeSyncContext:
    return TimeSyncContext(
        providers=[
            GetTimeApi(),
            AiSenseApi(),
            LocalTime(),
        ]
    )
