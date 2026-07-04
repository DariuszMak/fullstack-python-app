from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from src.backend.api.models.weather_score_response import BestScoreResponse
from src.ui.pyside_ui.dialog_windows.main_window.main_window import MainWindow

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget
    from pytestqt.qtbot import QtBot


def make_response() -> BestScoreResponse:
    return BestScoreResponse(
        results=[],
        min_threshold=20.0,
        max_threshold=25.0,
        penalize_rain=True,
        start_day=0,
    )


def widgets_in_layout(window: MainWindow) -> list[QWidget]:
    layout = window._ui.frame_query_parameters
    widgets: list[QWidget] = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is None:
            continue
        widget = item.widget()
        if widget is not None:
            widgets.append(widget)
    return widgets


def test_sliders_have_default_values(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    assert window._forecast_days_slider.value() == 7
    assert window._start_day_slider.value() == 0


def test_sliders_are_added_to_query_parameters_layout(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    widgets = widgets_in_layout(window)

    assert window._forecast_days_slider in widgets
    assert window._start_day_slider in widgets
    assert window._forecast_days_label in widgets
    assert window._start_day_label in widgets


def test_forecast_days_label_updates_on_slider_change(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._forecast_days_slider.setValue(3)

    assert window._forecast_days_label.text() == "Forecast days: 3"


def test_start_day_label_updates_on_slider_change(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._start_day_slider.setValue(5)

    assert window._start_day_label.text() == "Start day: 5"


def test_sliders_respect_configured_ranges(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    assert window._forecast_days_slider.minimum() == 1
    assert window._forecast_days_slider.maximum() == 16
    assert window._start_day_slider.minimum() == 0
    assert window._start_day_slider.maximum() == 15


def test_fetch_weather_score_uses_current_forecast_days_and_start_day(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._forecast_days_slider.setValue(10)
    window._start_day_slider.setValue(2)

    response = make_response()
    window._httpx_client.fetch_weather_score = AsyncMock(return_value=response)  # type: ignore[method-assign]

    asyncio.run(window._fetch_weather_score())

    window._httpx_client.fetch_weather_score.assert_called_once_with(
        apparent_temperature_min_threshold=18.0,
        apparent_temperature_max_threshold=25.0,
        penalize_rain=True,
        forecast_days=10,
        start_day=2,
    )


def test_start_day_slider_cannot_reach_or_exceed_forecast_days_slider(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._forecast_days_slider.setValue(5)
    window._start_day_slider.setValue(10)

    assert window._start_day_slider.value() < window._forecast_days_slider.value()


def test_forecast_days_slider_cannot_reach_or_go_below_start_day_slider(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._start_day_slider.setValue(8)
    window._forecast_days_slider.setValue(3)

    assert window._forecast_days_slider.value() > window._start_day_slider.value()


def test_start_day_slider_clamps_to_just_below_forecast_days(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._forecast_days_slider.setValue(7)
    window._start_day_slider.setValue(7)

    assert window._start_day_slider.value() == 6


def test_forecast_days_slider_clamps_to_just_above_start_day(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._start_day_slider.setValue(5)
    window._forecast_days_slider.setValue(5)

    assert window._forecast_days_slider.value() == 6