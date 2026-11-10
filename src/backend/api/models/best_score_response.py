from __future__ import annotations

from pydantic import BaseModel


class PlaceBestScoreRecord(BaseModel):
    key: str
    name: str
    latitude: float
    longitude: float
    timezone: str
    score: float
    percentage_score: float = 0.0


class BestScoreResponse(BaseModel):
    results: list[PlaceBestScoreRecord]
    min_threshold: float
    max_threshold: float
    penalize_rain: bool
    start_day: int
