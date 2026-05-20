from datetime import datetime

from .time_provider import TimeProvider


class TimeSyncContext:
    def __init__(self, providers: list[TimeProvider]) -> None:
        if not providers:
            raise ValueError("At least one TimeProvider is required.")
        self._providers = providers

    async def get_current_time(self) -> datetime:
        for provider in self._providers:
            result = await provider.fetch_time()
            if result is not None:
                return result

        raise RuntimeError("All time providers failed and no fallback was available.")