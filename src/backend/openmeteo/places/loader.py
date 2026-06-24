from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from src.backend.openmeteo.places.place import Place

PLACES_JSON_PATH = Path(__file__).parent / "places.json"


class PlaceModel(BaseModel):
    name: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    timezone: str = "Europe/Berlin"


def load_places(path: Path = PLACES_JSON_PATH) -> dict[str, Place]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {key: Place(**PlaceModel.model_validate(value).model_dump()) for key, value in raw.items()}
