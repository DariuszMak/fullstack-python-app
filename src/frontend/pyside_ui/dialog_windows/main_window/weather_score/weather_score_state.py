from dataclasses import dataclass

from src.backend.api.models.weather_score_response import PlaceBestScoreRecord


@dataclass(frozen=True)
class WeatherScoreCardData:
    rank: int
    place: PlaceBestScoreRecord


@dataclass(frozen=True)
class WeatherScoreState:
    is_loading: bool = False
    cards: tuple[WeatherScoreCardData, ...] = ()
    error: str | None = None
    min_threshold: float = 0.0
    max_threshold: float = 0.0
    penalize_rain: bool = False
    start_day: int = 0
