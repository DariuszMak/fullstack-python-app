from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.backend.api.models.weather_score_response import PlaceBestScoreRecord
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score.weather_score_renderer import (
    ERROR_STYLE,
    INFO_STYLE,
    WeatherScoreRenderer,
)
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score.weather_score_state import (
    WeatherScoreCardData,
    WeatherScoreState,
)
from src.frontend.pyside_ui.widgets.weather_score_card import WeatherScoreCard

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def make_place(key: str, score: float, percentage: float = 1.0) -> PlaceBestScoreRecord:
    return PlaceBestScoreRecord(
        key=key,
        name=key.title(),
        latitude=51.1,
        longitude=17.0,
        timezone="Europe/Warsaw",
        score=score,
        percentage_score=percentage,
    )


def make_cards_state() -> WeatherScoreState:
    return WeatherScoreState(
        cards=(
            WeatherScoreCardData(rank=1, place=make_place("krakow", 0.8, 1.0)),
            WeatherScoreCardData(rank=2, place=make_place("wroclaw", 0.5, 0.0)),
        )
    )


def make_renderer(qtbot: QtBot) -> tuple[WeatherScoreRenderer, QVBoxLayout]:
    container = QWidget()
    qtbot.addWidget(container)
    layout = QVBoxLayout(container)
    return WeatherScoreRenderer(layout), layout


def cards_in(layout: QVBoxLayout) -> list[WeatherScoreCard]:
    cards: list[WeatherScoreCard] = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is None:
            continue
        widget = item.widget()
        if isinstance(widget, WeatherScoreCard):
            cards.append(widget)
    return cards


def labels_in(layout: QVBoxLayout) -> list[QLabel]:
    labels: list[QLabel] = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is None:
            continue
        widget = item.widget()
        if isinstance(widget, QLabel):
            labels.append(widget)
    return labels


def test_render_cards_creates_one_card_per_entry(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    renderer.render(make_cards_state())

    assert len(cards_in(layout)) == 2
    assert labels_in(layout) == []


def test_render_cards_preserves_state_order(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    renderer.render(make_cards_state())

    cards = cards_in(layout)
    assert cards[0].name == "Krakow"
    assert cards[1].name == "Wroclaw"


def test_render_cards_assigns_rank_labels(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    renderer.render(make_cards_state())

    cards = cards_in(layout)
    assert cards[0]._rank_label.text() == "#1"
    assert cards[1]._rank_label.text() == "#2"


def test_render_cards_appends_trailing_stretch(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    renderer.render(make_cards_state())

    last_item = layout.itemAt(layout.count() - 1)
    assert last_item is not None
    assert last_item.widget() is None
    assert layout.count() == 3


def test_render_loading_shows_info_message(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    renderer.render(WeatherScoreState(is_loading=True))

    labels = labels_in(layout)
    assert len(labels) == 1
    assert labels[0].text() == "Fetching weather score..."
    assert labels[0].styleSheet() == INFO_STYLE
    assert labels[0].wordWrap() is True
    assert cards_in(layout) == []


def test_render_error_shows_error_message(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    renderer.render(WeatherScoreState(error="test_message"))

    labels = labels_in(layout)
    assert len(labels) == 1
    assert labels[0].text() == "Failed to fetch weather score: test_message"
    assert labels[0].styleSheet() == ERROR_STYLE
    assert labels[0].wordWrap() is True


def test_render_empty_cards_shows_no_matching_places_message(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    renderer.render(WeatherScoreState())

    labels = labels_in(layout)
    assert len(labels) == 1
    assert labels[0].text() == "No matching places found."
    assert labels[0].styleSheet() == INFO_STYLE
    assert cards_in(layout) == []


def test_render_loading_takes_precedence_over_error_and_cards(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)
    state = WeatherScoreState(
        is_loading=True,
        error="ignored",
        cards=make_cards_state().cards,
    )

    renderer.render(state)

    labels = labels_in(layout)
    assert [label.text() for label in labels] == ["Fetching weather score..."]
    assert cards_in(layout) == []


def test_render_error_takes_precedence_over_cards(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)
    state = WeatherScoreState(error="boom", cards=make_cards_state().cards)

    renderer.render(state)

    assert [label.text() for label in labels_in(layout)] == ["Failed to fetch weather score: boom"]
    assert cards_in(layout) == []


def test_render_replaces_previous_cards(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)
    renderer.render(make_cards_state())
    assert len(cards_in(layout)) == 2

    single = WeatherScoreState(cards=make_cards_state().cards[:1])
    renderer.render(single)

    assert len(cards_in(layout)) == 1


def test_render_message_replaces_cards(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)
    renderer.render(make_cards_state())

    renderer.render(WeatherScoreState(error="boom"))

    assert cards_in(layout) == []
    assert len(labels_in(layout)) == 1


def test_render_cards_replaces_message(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)
    renderer.render(WeatherScoreState(is_loading=True))

    renderer.render(make_cards_state())

    assert labels_in(layout) == []
    assert len(cards_in(layout)) == 2


def test_render_repeatedly_does_not_accumulate_items(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    for _ in range(5):
        renderer.render(make_cards_state())

    assert layout.count() == 3


def test_render_message_leaves_message_and_stretch_only(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)

    renderer.render(WeatherScoreState(is_loading=True))

    assert layout.count() == 2


def test_render_on_empty_layout_does_not_fail(qtbot: QtBot) -> None:
    renderer, layout = make_renderer(qtbot)
    assert layout.count() == 0

    renderer.render(WeatherScoreState())

    assert layout.count() == 2
