import openmeteo_requests
import requests_cache
from retry_requests import retry  # type: ignore


def build_openmeteo_client(
    cache_name: str = ".cache",
    expire_after: int = 3600,
    retries: int = 5,
    backoff_factor: float = 0.2,
) -> openmeteo_requests.Client:
    cache_session = requests_cache.CachedSession(cache_name, expire_after=expire_after)
    retry_session = retry(cache_session, retries=retries, backoff_factor=backoff_factor)
    return openmeteo_requests.Client(session=retry_session)
