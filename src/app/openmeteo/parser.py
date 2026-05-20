import pandas as pd
from openmeteo_sdk.VariablesWithTime import VariablesWithTime  # type: ignore


def parse_hourly_dataframe(hourly: VariablesWithTime, utc_offset_seconds: int) -> pd.DataFrame:
    date_range = pd.date_range(
        start=pd.to_datetime(hourly.Time() + utc_offset_seconds, unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd() + utc_offset_seconds, unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    )

    return pd.DataFrame({
        "date": date_range,
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "cloud_cover": hourly.Variables(1).ValuesAsNumpy(),
        "precipitation": hourly.Variables(2).ValuesAsNumpy(),
        "apparent_temperature": hourly.Variables(3).ValuesAsNumpy(),
        "soil_temperature_6cm": hourly.Variables(4).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(5).ValuesAsNumpy(),
        "surface_pressure": hourly.Variables(6).ValuesAsNumpy(),
        "wind_speed_10m": hourly.Variables(7).ValuesAsNumpy(),
        "wind_direction_10m": hourly.Variables(8).ValuesAsNumpy(),
        "wind_gusts_10m": hourly.Variables(9).ValuesAsNumpy(),
        "soil_moisture_0_to_1cm": hourly.Variables(10).ValuesAsNumpy(),
    })


def parse_daily_dataframe(daily: VariablesWithTime, utc_offset_seconds: int) -> pd.DataFrame:
    date_range = pd.date_range(
        start=pd.to_datetime(daily.Time() + utc_offset_seconds, unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd() + utc_offset_seconds, unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left",
    )

    return pd.DataFrame({
        "date": date_range,
        "sunshine_duration": daily.Variables(0).ValuesAsNumpy(),
        "uv_index_max": daily.Variables(1).ValuesAsNumpy(),
        "apparent_temperature_max": daily.Variables(2).ValuesAsNumpy(),
        "apparent_temperature_min": daily.Variables(3).ValuesAsNumpy(),
        "sunrise": daily.Variables(4).ValuesInt64AsNumpy(),
        "sunset": daily.Variables(5).ValuesInt64AsNumpy(),
        "daylight_duration": daily.Variables(6).ValuesAsNumpy(),
        "rain_sum": daily.Variables(7).ValuesAsNumpy(),
        "temperature_2m_max": daily.Variables(8).ValuesAsNumpy(),
        "temperature_2m_min": daily.Variables(9).ValuesAsNumpy(),
    })
