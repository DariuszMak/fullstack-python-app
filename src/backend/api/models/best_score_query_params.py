from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class BestScoreQueryParams(BaseModel):
    apparent_temperature_threshold: float = Field(
        default=20.0, description="Minimum apparent temperature (°C) to earn score points"
    )
    penalize_rain: bool = Field(
        default=True, description="When True, any rain in the forecast multiplies the place score by 0"
    )
    forecast_days: int = Field(default=3, ge=1, le=16, description="Number of forecast days to fetch (1-16)")
    start_day: int = Field(
        default=0,
        ge=0,
        description="First day offset from today (0 = today) to include in scoring",
    )

    @model_validator(mode="after")
    def _validate_day_range(self) -> BestScoreQueryParams:
        if self.start_day >= self.forecast_days:
            raise ValueError(f"start_day ({self.start_day}) must be less than forecast_days ({self.forecast_days})")

        return self
