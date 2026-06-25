from __future__ import annotations

from pytestqt.qtbot import QtBot

from src.backend.api.models.weather_score_response import PlaceBestScoreRecord
from src.ui.pyside_ui.dialog_windows.weather_score_card import WeatherScoreCard


def make_place(score: float = 0.5, name: str = "Wroclaw") -> PlaceBestScoreRecord:
    return PlaceBestScoreRecord(
        key="wroclaw",
        name=name,
        latitude=51.1,
        longitude=17.0,
        timezone="Europe/Warsaw",
        score=score,
    )


def test_card_displays_name_and_score(qtbot: QtBot) -> None:
    place = make_place(score=0.42)
    card = WeatherScoreCard(place, rank=1)
    qtbot.addWidget(card)

    assert card.name == "Wroclaw"
    assert card.score_text == "0.42"
    assert card.score_value == 42


def test_card_shows_rank_label(qtbot: QtBot) -> None:
    place = make_place()
    card = WeatherScoreCard(place, rank=3)
    qtbot.addWidget(card)

    assert card._rank_label.text() == "#3"


def test_card_without_rank_has_empty_rank_label(qtbot: QtBot) -> None:
    place = make_place()
    card = WeatherScoreCard(place)
    qtbot.addWidget(card)

    assert card._rank_label.text() == ""


def test_card_tooltip_contains_coordinates(qtbot: QtBot) -> None:
    place = make_place()
    card = WeatherScoreCard(place)
    qtbot.addWidget(card)

    assert "51.1000" in card.toolTip()
    assert "17.0000" in card.toolTip()
    assert "Europe/Warsaw" in card.toolTip()


def test_set_score_clamps_value_above_one(qtbot: QtBot) -> None:
    place = make_place(score=1.5)
    card = WeatherScoreCard(place)
    qtbot.addWidget(card)

    assert card.score_value == 100


def test_set_score_clamps_value_below_zero(qtbot: QtBot) -> None:
    place = make_place(score=-0.5)
    card = WeatherScoreCard(place)
    qtbot.addWidget(card)

    assert card.score_value == 0


def test_color_for_score_thresholds() -> None:
    assert WeatherScoreCard._color_for_score(0.9) == "rgb(46, 204, 113)"
    assert WeatherScoreCard._color_for_score(0.5) == "rgb(241, 196, 15)"
    assert WeatherScoreCard._color_for_score(0.1) == "rgb(231, 76, 60)"