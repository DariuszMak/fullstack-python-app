from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent

from src.backend.api.models.weather_score_response import PlaceBestScoreRecord
from src.frontend.pyside_ui.widgets.weather_score_card import WeatherScoreCard

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

DIALOG_PATH = "src.frontend.pyside_ui.widgets.weather_score_card.WeatherDetailsDialog"


def make_place(
    score: float = 0.5,
    percentage_score: float = 0.5,
    name: str = "Wroclaw",
) -> PlaceBestScoreRecord:
    return PlaceBestScoreRecord(
        key="wroclaw",
        name=name,
        latitude=51.1,
        longitude=17.0,
        timezone="Europe/Warsaw",
        score=score,
        percentage_score=percentage_score,
    )


def make_mouse_event(event_type: QMouseEvent.Type, button: Qt.MouseButton) -> QMouseEvent:
    return QMouseEvent(
        event_type,
        QPointF(5, 5),
        button,
        button,
        Qt.KeyboardModifier.NoModifier,
    )


def test_card_uses_pointing_hand_cursor(qtbot: QtBot) -> None:
    card = WeatherScoreCard(make_place())
    qtbot.addWidget(card)

    assert card.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_left_click_opens_details_dialog(qtbot: QtBot) -> None:
    place = make_place()
    card = WeatherScoreCard(place, rank=2)
    qtbot.addWidget(card)
    card.show()

    with patch(DIALOG_PATH) as dialog_cls:
        qtbot.mouseClick(card, Qt.MouseButton.LeftButton)  # type: ignore[no-untyped-call]

    dialog_cls.assert_called_once_with(place, rank=2, parent=card.window())
    dialog_cls.return_value.exec.assert_called_once_with()


def test_left_click_without_rank_passes_none(qtbot: QtBot) -> None:
    place = make_place()
    card = WeatherScoreCard(place)
    qtbot.addWidget(card)
    card.show()

    with patch(DIALOG_PATH) as dialog_cls:
        qtbot.mouseClick(card, Qt.MouseButton.LeftButton)  # type: ignore[no-untyped-call]

    dialog_cls.assert_called_once_with(place, rank=None, parent=card.window())


def test_right_click_does_not_open_details_dialog(qtbot: QtBot) -> None:
    card = WeatherScoreCard(make_place())
    qtbot.addWidget(card)
    card.show()

    with patch(DIALOG_PATH) as dialog_cls:
        qtbot.mouseClick(card, Qt.MouseButton.RightButton)  # type: ignore[no-untyped-call]

    dialog_cls.assert_not_called()


def test_release_outside_card_does_not_open_details_dialog(qtbot: QtBot) -> None:
    card = WeatherScoreCard(make_place())
    qtbot.addWidget(card)
    card.show()

    with patch(DIALOG_PATH) as dialog_cls:
        qtbot.mousePress(card, Qt.MouseButton.LeftButton)  # type: ignore[no-untyped-call]
        qtbot.mouseRelease(card, Qt.MouseButton.LeftButton, pos=QPoint(-10, -10))  # type: ignore[no-untyped-call]

    dialog_cls.assert_not_called()


def test_left_press_is_accepted(qtbot: QtBot) -> None:
    card = WeatherScoreCard(make_place())
    qtbot.addWidget(card)

    event = make_mouse_event(QMouseEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton)
    event.ignore()

    card.mousePressEvent(event)

    assert event.isAccepted() is True


def test_show_details_dialog_executes_dialog(qtbot: QtBot) -> None:
    place = make_place()
    card = WeatherScoreCard(place, rank=1)
    qtbot.addWidget(card)

    with patch(DIALOG_PATH) as dialog_cls:
        card.show_details_dialog()

    dialog_cls.assert_called_once_with(place, rank=1, parent=card.window())
    dialog_cls.return_value.exec.assert_called_once_with()


def test_card_displays_name_and_score(qtbot: QtBot) -> None:
    place = make_place(score=0.42, percentage_score=0.42)
    card = WeatherScoreCard(place, rank=1)
    qtbot.addWidget(card)

    assert card.name == "Wroclaw"
    assert card.score_text == "0.42"
    assert card.score_value == 42


def test_card_displays_calculated_score_separately_from_raw_score(qtbot: QtBot) -> None:
    place = make_place(score=0.91, percentage_score=0.2)
    card = WeatherScoreCard(place, rank=1)
    qtbot.addWidget(card)

    assert card.score_text == "0.91"
    assert card._calculated_score_label.text() == "0.20"
    assert card.score_value == 20


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
    place = make_place(score=0.9, percentage_score=1.5)
    card = WeatherScoreCard(place)
    qtbot.addWidget(card)

    assert card.score_value == 100


def test_set_score_clamps_value_below_zero(qtbot: QtBot) -> None:
    place = make_place(score=0.1, percentage_score=-0.5)
    card = WeatherScoreCard(place)
    qtbot.addWidget(card)

    assert card.score_value == 0


def test_set_score_updates_both_labels_on_call(qtbot: QtBot) -> None:
    place = make_place(score=0.3, percentage_score=0.3)
    card = WeatherScoreCard(place)
    qtbot.addWidget(card)

    card.set_score(0.77, 0.6)

    assert card.score_text == "0.77"
    assert card._calculated_score_label.text() == "0.60"
    assert card.score_value == 60


def test_color_for_score_thresholds() -> None:
    assert WeatherScoreCard._color_for_score(0.9) == "rgb(46, 204, 113)"
    assert WeatherScoreCard._color_for_score(0.5) == "rgb(241, 196, 15)"
    assert WeatherScoreCard._color_for_score(0.1) == "rgb(231, 76, 60)"
