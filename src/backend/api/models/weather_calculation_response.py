from datetime import datetime

from pydantic import BaseModel, Field

class WeatherQueryParams(BaseModel):
    Temperature: float = Field(..., description="Temperature")
    