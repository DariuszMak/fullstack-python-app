from datetime import datetime

import structlog

from src.api.time_provider.http_time_provider import HttpTimeProvider

logger = structlog.get_logger(__name__)

class GetTimeApiProvider(HttpTimeProvider):
    def __init__(self) -> None:
        super().__init__(
            url="https://gettimeapi.dev/v1/time?timezone=UTC",
            datetime_key="iso8601",
        )

