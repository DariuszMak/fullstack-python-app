from typing import Any

import openmeteo_requests
import pandas as pd
import structlog

from src.backend.openmeteo.client_builder import build_openmeteo_client
from src.backend.openmeteo.parse import parse_daily_dataframe, parse_hourly_dataframe
from src.backend.openmeteo.request_builder import API_URL, build_request_parameters

logger = structlog.get_logger(__name__)


def _fetch_weather_response(client: openmeteo_requests.Client, parameters: dict[str, Any]) -> Any:
    log = logger.bind(api_url=API_URL, parameters=parameters)
    log.info("requesting_weather_data")

    try:
        responses = client.weather_api(API_URL, params=parameters)
        return responses[0]
    except Exception as e:
        log.exception("weather_api_request_failed", error=str(e))
        raise


def gather_data(parameters: dict[str, Any] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    client = build_openmeteo_client()

    if parameters is None:
        parameters = build_request_parameters()

    response = _fetch_weather_response(client, parameters)
    utc_offset = response.UtcOffsetSeconds()

    logger.info("parsing_weather_response", utc_offset=utc_offset)

    hourly = response.Hourly()
    if hourly is not None:
        hourly_df = parse_hourly_dataframe(hourly, utc_offset)
    else:
        hourly_df = pd.DataFrame()

    daily = response.Daily()
    if daily is not None:
        daily_df = parse_daily_dataframe(daily, utc_offset)
    else:
        daily_df = pd.DataFrame()

    logger.info(
        "weather_data_gathered",
        hourly_rows=len(hourly_df),
        daily_rows=len(daily_df),
    )

    return hourly_df, daily_df
