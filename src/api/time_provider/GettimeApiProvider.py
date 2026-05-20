from src.api.time_provider.time_provider import HttpTimeProvider


class GettimeApiProvider(HttpTimeProvider):
    def __init__(self) -> None:
        super().__init__(
            url="https://gettimeapi.dev/v1/time?timezone=UTC",
            datetime_key="iso8601",
        )