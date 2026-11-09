from __future__ import annotations

from pydantic import BaseModel, Field


class WeatherQueryParams(BaseModel):
    latitude: float = Field(default=51.9727, description="Latitude of the location")
    longitude: float = Field(default=17.5026, description="Longitude of the location")
    timezone: str = Field(default="Europe/Berlin", description="IANA timezone string")
    forecast_days: int = Field(default=3, ge=1, le=16, description="Number of forecast days (1-16)")
