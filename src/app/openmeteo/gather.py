from typing import Any

import pandas as pd
import structlog

from src.app.openmeteo.client_builder import build_openmeteo_client
from src.app.openmeteo.params import API_URL, build_request_params
from src.app.openmeteo.parser import parse_daily_dataframe, parse_hourly_dataframe

logger = structlog.get_logger(__name__)


def fetch_weather_response(client: Any, params: dict[str, Any]) -> Any:
    log = logger.bind(api_url=API_URL, params=params)
    log.info("requesting_weather_data")

    try:
        responses = client.weather_api(API_URL, params=params)
        return responses[0]
    except Exception as e:
        log.exception("weather_api_request_failed", error=str(e))
        raise


def gather_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    client = build_openmeteo_client()
    params = build_request_params()

    response = fetch_weather_response(client, params)
    utc_offset = response.UtcOffsetSeconds()

    logger.info("parsing_weather_response", utc_offset=utc_offset)

    hourly_df = parse_hourly_dataframe(response.Hourly(), utc_offset)
    daily_df = parse_daily_dataframe(response.Daily(), utc_offset)

    logger.info(
        "weather_data_gathered",
        hourly_rows=len(hourly_df),
        daily_rows=len(daily_df),
        hourly_preview=hourly_df.head(1).to_dict(orient="records"),
        daily_preview=daily_df.head(1).to_dict(orient="records"),
    )

    return hourly_df, daily_df
