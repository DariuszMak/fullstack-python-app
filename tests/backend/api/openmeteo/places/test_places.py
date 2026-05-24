import pytest

from src.backend.openmeteo.places.place import Place
from src.backend.openmeteo.places.places import DEFAULT_PLACE, LATITUDE, LONGITUDE, PLACES, TIMEZONE
from src.backend.openmeteo.request_builder import build_request_parameters
from tests.backend.api.openmeteo.test_openmeto import EXPECTED_PLACE_KEYS


def test_places_contains_all_expected_keys() -> None:
    assert set(PLACES.keys()) == EXPECTED_PLACE_KEYS


def test_all_places_are_place_instances() -> None:
    for key, place in PLACES.items():
        assert isinstance(place, Place), f"{key} is not a Place instance"


def test_all_places_have_non_empty_name() -> None:
    for key, place in PLACES.items():
        assert place.name, f"{key} has an empty name"


def test_all_places_have_valid_latitude() -> None:
    for key, place in PLACES.items():
        assert -90.0 <= place.latitude <= 90.0, f"{key} has invalid latitude {place.latitude}"


def test_all_places_have_valid_longitude() -> None:
    for key, place in PLACES.items():
        assert -180.0 <= place.longitude <= 180.0, f"{key} has invalid longitude {place.longitude}"


def test_all_places_have_non_empty_timezone() -> None:
    for key, place in PLACES.items():
        assert place.timezone, f"{key} has an empty timezone"


def test_place_is_frozen() -> None:
    from dataclasses import FrozenInstanceError

    place = PLACES["jarocin"]
    with pytest.raises(FrozenInstanceError, match="cannot assign to field"):
        setattr(place, "latitude", 0.0)  # noqa: B010


def test_default_place_is_jarocin() -> None:
    assert DEFAULT_PLACE is PLACES["jarocin"]


def test_backwards_compat_latitude() -> None:
    assert pytest.approx(PLACES["jarocin"].latitude) == LATITUDE


def test_backwards_compat_longitude() -> None:
    assert pytest.approx(PLACES["jarocin"].longitude) == LONGITUDE


def test_backwards_compat_timezone() -> None:
    assert PLACES["jarocin"].timezone == TIMEZONE


def test_sea_places_are_in_northern_poland() -> None:
    sea_keys = {"swinoujscie", "mielno", "leba", "debki", "hel", "gdansk"}
    for key in sea_keys:
        assert PLACES[key].latitude > 53.0, f"{key} latitude unexpectedly low"


def test_mountain_towns_are_in_southern_poland() -> None:
    mountain_keys = {"karpacz", "zakopane"}
    for key in mountain_keys:
        assert PLACES[key].latitude < 51.0, f"{key} latitude unexpectedly high"


def test_mountain_peaks_are_in_southern_poland() -> None:
    peak_keys = {"rysy", "giewont", "sniezka"}
    for key in peak_keys:
        assert PLACES[key].latitude < 51.0, f"{key} latitude unexpectedly high"


def test_returns_required_keys() -> None:
    parameters = build_request_parameters()
    for key in ("latitude", "longitude", "daily", "hourly", "timezone", "forecast_days"):
        assert key in parameters


def test_default_coordinates() -> None:
    parameters = build_request_parameters()
    assert parameters["latitude"] == LATITUDE
    assert parameters["longitude"] == LONGITUDE


def test_timezone_default() -> None:
    assert build_request_parameters()["timezone"] == TIMEZONE


def test_build_request_parameters_from_place() -> None:
    place = PLACES["zakopane"]
    params = build_request_parameters(latitude=place.latitude, longitude=place.longitude, timezone=place.timezone)
    assert params["latitude"] == pytest.approx(place.latitude)
    assert params["longitude"] == pytest.approx(place.longitude)
    assert params["timezone"] == place.timezone
