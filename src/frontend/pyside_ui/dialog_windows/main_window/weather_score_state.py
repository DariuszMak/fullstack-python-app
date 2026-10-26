from dataclasses import dataclass, field


@dataclass
class WeatherScoreState:
    is_loading: bool = False
    cards: list[dict] = field(default_factory=list)
    error: str | None = None
    min_threshold: float = 0.0
    max_threshold: float = 0.0
    penalize_rain: bool = False
    start_day: int = 0
