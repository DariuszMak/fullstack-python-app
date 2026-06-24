import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.backend.openmeteo.places.loader import PLACES_JSON_PATH, PlaceModel, load_places
from src.backend.openmeteo.places.place import Place
from src.backend.openmeteo.places.places import PLACES


def _write_places(tmp_path: Path, data: dict) -> Path:
    file_path = tmp_path / "places.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_default_places_json_file_exists() -> None:
    assert PLACES_JSON_PATH.exists()


def test_load_places_returns_place_instances() -> None:
    places = load_places()
    for place in places.values():
        assert isinstance(place, Place)


def test_load_places_matches_module_level_places() -> None:
    places = load_places()
    assert places.keys() == PLACES.keys()


def test_load_places_values_match_module_level_places() -> None:
    places = load_places()
    for key, place in places.items():
        assert place == PLACES[key]


def test_load_places_applies_default_timezone(tmp_path: Path) -> None:
    data = {"test": {"name": "Test", "latitude": 1.0, "longitude": 1.0}}
    file_path = _write_places(tmp_path, data)

    places = load_places(file_path)

    assert places["test"].timezone == "Europe/Berlin"


def test_load_places_uses_explicit_timezone(tmp_path: Path) -> None:
    data = {"test": {"name": "Test", "latitude": 1.0, "longitude": 1.0, "timezone": "UTC"}}
    file_path = _write_places(tmp_path, data)

    places = load_places(file_path)

    assert places["test"].timezone == "UTC"


def test_load_places_preserves_keys(tmp_path: Path) -> None:
    data = {
        "alpha": {"name": "Alpha", "latitude": 1.0, "longitude": 1.0},
        "beta": {"name": "Beta", "latitude": 2.0, "longitude": 2.0},
    }
    file_path = _write_places(tmp_path, data)

    places = load_places(file_path)

    assert set(places.keys()) == {"alpha", "beta"}


def test_load_places_empty_file_returns_empty_dict(tmp_path: Path) -> None:
    file_path = _write_places(tmp_path, {})
    assert load_places(file_path) == {}


def test_load_places_rejects_invalid_latitude(tmp_path: Path) -> None:
    data = {"test": {"name": "Test", "latitude": 200.0, "longitude": 1.0}}
    file_path = _write_places(tmp_path, data)

    with pytest.raises(ValidationError):
        load_places(file_path)


def test_load_places_rejects_invalid_longitude(tmp_path: Path) -> None:
    data = {"test": {"name": "Test", "latitude": 1.0, "longitude": 200.0}}
    file_path = _write_places(tmp_path, data)

    with pytest.raises(ValidationError):
        load_places(file_path)


def test_load_places_rejects_missing_name(tmp_path: Path) -> None:
    data = {"test": {"latitude": 1.0, "longitude": 1.0}}
    file_path = _write_places(tmp_path, data)

    with pytest.raises(ValidationError):
        load_places(file_path)


def test_load_places_rejects_missing_latitude(tmp_path: Path) -> None:
    data = {"test": {"name": "Test", "longitude": 1.0}}
    file_path = _write_places(tmp_path, data)

    with pytest.raises(ValidationError):
        load_places(file_path)


def test_load_places_raises_for_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_places(missing_path)


def test_load_places_raises_for_invalid_json(tmp_path: Path) -> None:
    file_path = tmp_path / "places.json"
    file_path.write_text("not valid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_places(file_path)


def test_place_model_accepts_boundary_coordinates() -> None:
    model = PlaceModel(name="Edge", latitude=-90.0, longitude=180.0)
    assert model.latitude == pytest.approx(-90.0)
    assert model.longitude == pytest.approx(180.0)
