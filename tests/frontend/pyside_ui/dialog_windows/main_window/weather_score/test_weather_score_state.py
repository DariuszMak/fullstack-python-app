from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.backend.api.models.weather_score_response import PlaceBestScoreRecord
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score.weather_score_state import (
    WeatherScoreCardData,
    WeatherScoreState,
)


def make_place(key: str = "wroclaw", score: float = 0.5) -> PlaceBestScoreRecord:
    return PlaceBestScoreRecord(
        key=key,
        name=key.title(),
        latitude=51.1,
        longitude=17.0,
        timezone="Europe/Warsaw",
        score=score,
    )


def test_state_defaults() -> None:
    state = WeatherScoreState()

    assert state.is_loading is False
    assert state.cards == ()
    assert state.error is None
    assert state.min_threshold == pytest.approx(0.0)
    assert state.max_threshold == pytest.approx(0.0)
    assert state.penalize_rain is False
    assert state.start_day == 0


def test_state_is_frozen() -> None:
    state = WeatherScoreState()

    with pytest.raises(FrozenInstanceError):
        state.is_loading = True  # type: ignore[misc]


def test_card_data_is_frozen() -> None:
    card = WeatherScoreCardData(rank=1, place=make_place())

    with pytest.raises(FrozenInstanceError):
        card.rank = 2  # type: ignore[misc]


def test_card_data_stores_rank_and_place() -> None:
    place = make_place()

    card = WeatherScoreCardData(rank=3, place=place)

    assert card.rank == 3
    assert card.place is place


def test_state_equality_for_same_values() -> None:
    card = WeatherScoreCardData(rank=1, place=make_place())

    first = WeatherScoreState(cards=(card,), error="x", min_threshold=1.0, max_threshold=2.0)
    second = WeatherScoreState(cards=(card,), error="x", min_threshold=1.0, max_threshold=2.0)

    assert first == second


def test_state_inequality_for_different_values() -> None:
    assert WeatherScoreState(is_loading=True) != WeatherScoreState(is_loading=False)


def test_state_stores_all_fields() -> None:
    card = WeatherScoreCardData(rank=1, place=make_place())

    state = WeatherScoreState(
        is_loading=True,
        cards=(card,),
        error="oops",
        min_threshold=10.0,
        max_threshold=20.0,
        penalize_rain=True,
        start_day=2,
    )

    assert state.is_loading is True
    assert state.cards == (card,)
    assert state.error == "oops"
    assert state.min_threshold == pytest.approx(10.0)
    assert state.max_threshold == pytest.approx(20.0)
    assert state.penalize_rain is True
    assert state.start_day == 2
