from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.api.models.weather_score_response import BestScoreResponse, PlaceBestScoreRecord
from src.ui.pyside_ui.dialog_windows.main_window import MainWindow

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def make_response() -> BestScoreResponse:
    return BestScoreResponse(
        results=[
            PlaceBestScoreRecord(
                key="wroclaw",
                name="Wroclaw",
                latitude=51.1,
                longitude=17.0,
                timezone="Europe/Warsaw",
                score=0.8,
            ),
            PlaceBestScoreRecord(
                key="krakow",
                name="Krakow",
                latitude=50.0,
                longitude=19.9,
                timezone="Europe/Warsaw",
                score=0.5,
            ),
        ],
        min_threshold=20.0,
        max_threshold=25.0,
        penalize_rain=True,
        start_day=0,
    )


def test_format_weather_score_includes_all_places() -> None:
    response = make_response()

    text = MainWindow._format_weather_score(response)

    assert "Wroclaw: 0.80" in text
    assert "Krakow: 0.50" in text
    assert "20.0" in text
    assert "25.0" in text
    assert "Penalize rain: True" in text
    assert "Start day offset: 0" in text


def test_apply_weather_score_sets_text_browser(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    response = make_response()

    window._apply_weather_score(response)

    text = window._ui.weatherScoreTextBrowser.toPlainText()

    assert "Wroclaw: 0.80" in text
    assert "Krakow: 0.50" in text


def test_check_weather_score_creates_task(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    mock_task = MagicMock()

    def fake_create_task(coro: Any) -> MagicMock:
        coro.close()
        return mock_task

    with patch(
        "src.ui.pyside_ui.dialog_windows.main_window.asyncio.create_task",
        side_effect=fake_create_task,
    ) as mock_create_task:
        window.check_weather_score()

        mock_create_task.assert_called_once()
        assert window._weather_score_task is mock_task


def test_check_weather_score_skips_when_task_already_running(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    existing_task = MagicMock()
    existing_task.done.return_value = False
    window._weather_score_task = existing_task

    with patch("src.ui.pyside_ui.dialog_windows.main_window.asyncio.create_task") as mock_create_task:
        window.check_weather_score()

        mock_create_task.assert_not_called()


def test_fetch_weather_score_applies_result_on_success(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    response = make_response()
    window._time_client.fetch_weather_score = AsyncMock(return_value=response)  # type: ignore[method-assign]

    asyncio.run(window._fetch_weather_score())

    text = window._ui.weatherScoreTextBrowser.toPlainText()
    assert "Wroclaw: 0.80" in text


def test_fetch_weather_score_shows_error_on_failure(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._time_client.fetch_weather_score = AsyncMock(side_effect=RuntimeError("boom"))  # type: ignore[method-assign]

    asyncio.run(window._fetch_weather_score())

    text = window._ui.weatherScoreTextBrowser.toPlainText()
    assert "Failed to fetch weather score" in text
    assert "boom" in text
