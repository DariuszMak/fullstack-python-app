from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class BestScoreQueryParams(BaseModel):
    apparent_temperature_threshold: float = Field(
        default=20.0, description="Minimum apparent temperature (°C) to earn score points"
    )
    penalize_rain: bool = Field(
        default=True, description="When True, any rain in the forecast multiplies the place score by 0"
    )
    forecast_days: int = Field(default=16, ge=1, le=16, description="Number of forecast days to fetch (1-16)")
    start_day: int = Field(
        default=0,
        ge=0,
        description="First day offset from today (0 = today) to include in scoring",
    )
    end_day: int | None = Field(
        default=None,
        description=(
            "Exclusive end day offset from today. "
            "Defaults to forecast_days. Must satisfy start_day < end_day <= forecast_days."
        ),
    )

    @model_validator(mode="after")
    def _validate_day_range(self) -> BestScoreQueryParams:
        effective_end = self.end_day if self.end_day is not None else self.forecast_days

        if effective_end > self.forecast_days:
            raise ValueError(f"end_day ({effective_end}) cannot exceed forecast_days ({self.forecast_days})")
        if self.start_day >= effective_end:
            raise ValueError(f"start_day ({self.start_day}) must be less than end_day ({effective_end})")

        object.__setattr__(self, "end_day", effective_end)
        return self


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
    end_day: int
