from src.api.time_provider.time_provider import HttpTimeProvider


class AisenseApiProvider(HttpTimeProvider):
    def __init__(self) -> None:
        super().__init__(
            url="https://aisenseapi.com/services/v1/datetime",
            datetime_key="datetime",
        )
