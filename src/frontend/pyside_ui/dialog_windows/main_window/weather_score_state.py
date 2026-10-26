from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WeatherScoreState:
    is_loading: bool = False
    cards: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    min_threshold: float = 0.0
    max_threshold: float = 0.0
    penalize_rain: bool = False
    start_day: int = 0
