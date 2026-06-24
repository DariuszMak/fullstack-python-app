from src.backend.openmeteo.places.loader import load_places
from src.backend.openmeteo.places.place import Place

PLACES: dict[str, Place] = load_places()

DEFAULT_PLACE = PLACES["jarocin"]

LATITUDE: float = DEFAULT_PLACE.latitude
LONGITUDE: float = DEFAULT_PLACE.longitude
TIMEZONE: str = DEFAULT_PLACE.timezone
