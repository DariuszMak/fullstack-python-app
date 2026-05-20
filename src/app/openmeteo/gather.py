
import pandas as pd
import structlog

from src.app.openmeteo.client_builder import build_openmeteo_client
from src.app.openmeteo.fetch import fetch_weather_response
from src.app.openmeteo.parameters import build_request_parameters
from src.app.openmeteo.parser import parse_daily_dataframe, parse_hourly_dataframe

logger = structlog.get_logger(__name__)


def gather_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    client = build_openmeteo_client()
    parameters = build_request_parameters()

    response = fetch_weather_response(client, parameters)
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
