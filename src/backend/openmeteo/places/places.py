from src.backend.openmeteo.places.place import Place

PLACES: dict[str, Place] = {
    "jarocin": Place(name="Jarocin", latitude=51.9727, longitude=17.5026),
    "swinoujscie": Place(name="Świnoujście", latitude=53.9105, longitude=14.2471),
    "mielno": Place(name="Mielno", latitude=54.2609, longitude=16.0621),
    "leba": Place(name="Łeba", latitude=54.761, longitude=17.5555),
    "hel": Place(name="Hel", latitude=54.6038, longitude=18.8035),
    "gdansk": Place(name="Gdańsk", latitude=54.3523, longitude=18.6491),
    "karpacz": Place(name="Karpacz", latitude=50.7767, longitude=15.7559),
    "zakopane": Place(name="Zakopane", latitude=49.299, longitude=19.9489),
    "rysy": Place(name="Rysy", latitude=49.1791, longitude=20.0884),
    "giewont": Place(name="Giewont", latitude=49.2509, longitude=19.9343),
    "sniezka": Place(name="Śnieżka", latitude=50.7361, longitude=15.7398),
}

# Default place kept for backwards compatibility
DEFAULT_PLACE = PLACES["jarocin"]

LATITUDE: float = DEFAULT_PLACE.latitude
LONGITUDE: float = DEFAULT_PLACE.longitude
TIMEZONE: str = DEFAULT_PLACE.timezone
