from __future__ import annotations

from pydantic import BaseModel


class PlaceBestScoreRecord(BaseModel):
    key: str
    name: str
    latitude: float
    longitude: float
    timezone: str
    score: float


class BestScoreResponse(BaseModel):
    results: list[PlaceBestScoreRecord]
    threshold: float
    penalize_rain: bool
    start_day: int
