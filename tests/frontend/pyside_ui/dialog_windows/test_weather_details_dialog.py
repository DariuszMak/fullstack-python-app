from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from src.backend.api.models.weather_info_response import HourlyRecord, WeatherInfoResponse
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


def test_change_event_language_change_retranslates(
    dialog: WeatherDetailsDialog,
) -> None:
    event = QEvent(QEvent.Type.LanguageChange)

    with patch.object(dialog._ui, "retranslateUi") as retranslate:
        dialog.changeEvent(event)

    retranslate.assert_called_once_with(dialog)


def test_change_event_other_type_does_not_retranslate(
    dialog: WeatherDetailsDialog,
) -> None:
    event = QEvent(QEvent.Type.Resize)

    with patch.object(dialog._ui, "retranslateUi") as retranslate:
        dialog.changeEvent(event)

    retranslate.assert_not_called()


def test_btn_close_click_closes_dialog(dialog: WeatherDetailsDialog) -> None:
    dialog.show()
    assert dialog.isVisible() is True

    dialog._ui.btn_close.click()

    assert dialog.isVisible() is False


def test_close_event_calls_super(dialog: WeatherDetailsDialog) -> None:
    event = QCloseEvent()

    with patch(
        "src.frontend.pyside_ui.dialog_windows.weather_details_dialog.DraggableDialog.closeEvent"
    ) as super_close:
        dialog.closeEvent(event)

    super_close.assert_called_once_with(event)


def test_show_event_triggers_fetch(qtbot: QtBot) -> None:
    with (
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.style_window"),
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.center_window"),
    ):
        widget = WeatherDetailsDialog(make_place())
        qtbot.addWidget(widget)
        widget.show()
        qtbot.processEvents()

    assert widget._weather_info_task is not None


def test_update_plot_displays_curves(qtbot: QtBot) -> None:
    with (
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.style_window"),
        patch("src.frontend.pyside_ui.dialog_windows.weather_details_dialog.StyleLoader.center_window"),
    ):
        widget = WeatherDetailsDialog(make_place())
        qtbot.addWidget(widget)

        response = WeatherInfoResponse(
            hourly=[
                HourlyRecord(
                    date="2026-01-01T00:00:00+00:00",
                    temperature_2m=10.0,
                    cloud_cover=50.0,
                    precipitation=0.0,
                    apparent_temperature=8.0,
                    soil_temperature_6cm=12.0,
                    relative_humidity_2m=60.0,
                    surface_pressure=1013.0,
                    wind_speed_10m=5.0,
                    wind_direction_10m=180.0,
                    wind_gusts_10m=10.0,
                    soil_moisture_0_to_1cm=0.2,
                )
            ],
            daily=[],
            hourly_rows=1,
            daily_rows=0,
        )
        widget._update_plot(response)

    assert widget._plot_widget is not None
    curves = widget._plot_widget.plotDataItem()
    assert len(curves) == 2
