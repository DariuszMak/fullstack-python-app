from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QWidget

from src.backend.api.models.weather_score_response import PlaceBestScoreRecord
from src.frontend.pyside_ui.dialog_windows.weather_details_dialog import WeatherDetailsDialog

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


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


@pytest.fixture
def dialog(qtbot: QtBot) -> WeatherDetailsDialog:
    with (
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.style_window"),
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.center_window"),
    ):
        widget = WeatherDetailsDialog(make_place(score=0.42, percentage_score=0.8), rank=2)

    qtbot.addWidget(widget)
    return widget


def test_init_without_parent(dialog: WeatherDetailsDialog) -> None:
    assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_init_with_parent_calls_style_loader(qtbot: QtBot) -> None:
    parent = QWidget()
    qtbot.addWidget(parent)

    with (
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.style_window") as style_window,
        patch(
            "src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.center_window"
        ) as center_window,
    ):
        widget = WeatherDetailsDialog(make_place(), parent=parent)
        qtbot.addWidget(widget)

    style_window.assert_called_once_with(widget)
    center_window.assert_called_once_with(widget, parent)


def test_dialog_stores_place(dialog: WeatherDetailsDialog) -> None:
    assert dialog.place.key == "wroclaw"


def test_title_shows_place_name(dialog: WeatherDetailsDialog) -> None:
    assert dialog._title_label.text() == "Wroclaw"


def test_dialog_displays_place_data(dialog: WeatherDetailsDialog) -> None:
    assert dialog.value("name") == "Wroclaw"
    assert dialog.value("key") == "wroclaw"
    assert dialog.value("latitude") == "51.1000"
    assert dialog.value("longitude") == "17.0000"
    assert dialog.value("timezone") == "Europe/Warsaw"


def test_dialog_displays_scores(dialog: WeatherDetailsDialog) -> None:
    assert dialog.value("score") == "0.42"
    assert dialog.value("calculated_score") == "0.80"


def test_dialog_shows_rank(dialog: WeatherDetailsDialog) -> None:
    assert dialog.value("rank") == "#2"


def test_dialog_without_rank_shows_placeholder(qtbot: QtBot) -> None:
    with (
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.style_window"),
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.center_window"),
    ):
        widget = WeatherDetailsDialog(make_place())

    qtbot.addWidget(widget)

    assert widget.value("rank") == "-"


def test_btn_close_click_closes_dialog(dialog: WeatherDetailsDialog) -> None:
    dialog.show()
    assert dialog.isVisible() is True

    dialog._close_button.click()

    assert dialog.isVisible() is False


def test_close_event_calls_super(dialog: WeatherDetailsDialog) -> None:
    event = QCloseEvent()

    with patch(
        "src.frontend.pyside_ui.dialog_windows.weather_details_dialog.DraggableDialog.closeEvent"
    ) as super_close:
        dialog.closeEvent(event)

    super_close.assert_called_once_with(event)

