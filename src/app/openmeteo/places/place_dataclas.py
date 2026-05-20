from dataclasses import dataclass


@dataclass(frozen=True)
class Place:
    name: str
    latitude: float
    longitude: float
    timezone: str = "Europe/Berlin"
