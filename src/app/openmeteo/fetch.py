from typing import Any

import structlog

from src.app.openmeteo.parameters import API_URL

logger = structlog.get_logger(__name__)


def fetch_weather_response(client: Any, parameters: dict[str, Any]) -> Any:
    log = logger.bind(api_url=API_URL, parameters=parameters)
    log.info("requesting_weather_data")

    try:
        responses = client.weather_api(API_URL, parameters=parameters)
        return responses[0]
    except Exception as e:
        log.exception("weather_api_request_failed", error=str(e))
        raise
