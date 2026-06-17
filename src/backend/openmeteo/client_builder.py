import openmeteo_requests
import requests_cache
from requests_cache.backends.redis import RedisCache
from retry_requests import retry


def build_openmeteo_client(
    cache_name: str = "openmeteo_cache",
    expire_after: int = 3600,
    retries: int = 5,
    backoff_factor: float = 0.2,
) -> openmeteo_requests.Client:
    backend = RedisCache(host="localhost", port=6379)
    cache_session = requests_cache.CachedSession(cache_name, backend=backend, expire_after=expire_after)
    retry_session = retry(cache_session, retries=retries, backoff_factor=backoff_factor)
    return openmeteo_requests.Client(session=retry_session)
