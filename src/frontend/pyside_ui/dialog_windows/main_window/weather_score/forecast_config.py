from dataclasses import dataclass


@dataclass(frozen=True)
class ForecastConfig:
    forecast_days: int = 3
    start_day: int = 0
