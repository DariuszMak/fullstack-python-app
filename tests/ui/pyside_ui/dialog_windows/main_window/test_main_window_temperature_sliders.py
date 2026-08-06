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
    layout = window._ui.frame_generated_query_parameters
    widgets: list[QWidget] = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is None:
            continue
        widget = item.widget()
        if widget is not None:
            widgets.append(widget)
    return widgets


def test_temperature_sliders_have_default_values(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    assert window._min_temp_slider.value() == 18
    assert window._max_temp_slider.value() == 25


def test_sliders_are_added_to_query_parameters_layout(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    widgets = widgets_in_layout(window)

    assert window._min_temp_slider in widgets
    assert window._max_temp_slider in widgets
    assert window._min_temp_label in widgets
    assert window._max_temp_label in widgets


def test_min_temp_label_updates_on_slider_change(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._min_temp_slider.setValue(5)

    assert window._min_temp_label.text() == "Min apparent temperature: 5.0\u00b0C"


def test_max_temp_label_updates_on_slider_change(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._max_temp_slider.setValue(30)

    assert window._max_temp_label.text() == "Max apparent temperature: 30.0\u00b0C"


def test_min_temp_slider_cannot_reach_or_exceed_max_slider(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._max_temp_slider.setValue(25)
    window._min_temp_slider.setValue(30)

    assert window._min_temp_slider.value() < window._max_temp_slider.value()


def test_max_temp_slider_cannot_reach_or_go_below_min_slider(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._min_temp_slider.setValue(20)
    window._max_temp_slider.setValue(10)

    assert window._max_temp_slider.value() > window._min_temp_slider.value()


def test_fetch_weather_score_uses_current_slider_values(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._min_temp_slider.setValue(10)
    window._max_temp_slider.setValue(18)

    response = make_response()
    window._httpx_client.fetch_weather_score = AsyncMock(return_value=response)  # type: ignore[method-assign]

    asyncio.run(window._fetch_weather_score())

    window._httpx_client.fetch_weather_score.assert_called_once_with(
        apparent_temperature_min_threshold=10.0,
        apparent_temperature_max_threshold=18.0,
        penalize_rain=True,
        forecast_days=3,
        start_day=0,
    )
