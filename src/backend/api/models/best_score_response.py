from __future__ import annotations

from pydantic import BaseModel, Field


class BestScoreQueryParams(BaseModel):
    apparent_temperature_threshold: float = Field(
        default=20.0, description="Minimum apparent temperature (°C) to earn score points"
    )
    penalize_rain: bool = Field(
        default=True, description="When True, any rain in the forecast multiplies the place score by 0"
    )
    forecast_days: int = Field(default=16, ge=1, le=16, description="Number of forecast days to consider (1-16)")


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
