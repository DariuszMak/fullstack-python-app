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


def test_rain_penalty_checkbox_defaults_to_checked(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    assert window._penalize_rain_checkbox.isChecked() is True


def test_rain_penalty_checkbox_label_text(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    assert window._penalize_rain_checkbox.text() == "Penalize rain"


def test_rain_penalty_checkbox_is_added_to_query_parameters_layout(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    widgets = widgets_in_layout(window)

    assert window._penalize_rain_checkbox in widgets


def test_rain_penalty_checkbox_can_be_toggled(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._penalize_rain_checkbox.setChecked(False)

    assert window._penalize_rain_checkbox.isChecked() is False


def test_fetch_weather_score_sends_penalize_rain_true_when_checked(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._penalize_rain_checkbox.setChecked(True)

    response = make_response()
    window._httpx_client.fetch_weather_score = AsyncMock(return_value=response)  # type: ignore[method-assign]

    asyncio.run(window._fetch_weather_score())

    window._httpx_client.fetch_weather_score.assert_called_once_with(
        apparent_temperature_min_threshold=18.0,
        apparent_temperature_max_threshold=25.0,
        penalize_rain=True,
        forecast_days=3,
        start_day=0,
    )


def test_fetch_weather_score_sends_penalize_rain_false_when_unchecked(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._penalize_rain_checkbox.setChecked(False)

    response = make_response()
    window._httpx_client.fetch_weather_score = AsyncMock(return_value=response)  # type: ignore[method-assign]

    asyncio.run(window._fetch_weather_score())

    window._httpx_client.fetch_weather_score.assert_called_once_with(
        apparent_temperature_min_threshold=18.0,
        apparent_temperature_max_threshold=25.0,
        penalize_rain=False,
        forecast_days=3,
        start_day=0,
    )
