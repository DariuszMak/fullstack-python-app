from src.api.time_provider.time_provider import TimeProvider, logger


from datetime import datetime


class LocalTimeProvider(TimeProvider):
    async def fetch_time(self) -> datetime:
        dt = datetime.now().astimezone()
        logger.info("falling_back_to_local_time", timestamp=dt.isoformat())
        return dt