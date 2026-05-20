import structlog

from src.api.time_provider.strategy.interface.http_time_provider import HttpTimeProvider

logger = structlog.get_logger(__name__)


class AiSenseApiProvider(HttpTimeProvider):
    def __init__(self) -> None:
        super().__init__(
            url="https://aisenseapi.com/services/v1/datetime",
            datetime_key="datetime",
        )
