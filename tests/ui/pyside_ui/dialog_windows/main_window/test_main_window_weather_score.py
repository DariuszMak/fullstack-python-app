from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from src.ui.pyside_ui.dialog_windows.main_window.main_window import MainWindow

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_check_weather_score_creates_task(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    mock_task = MagicMock()

    def fake_create_task(coro: Any) -> MagicMock:
        coro.close()
        return mock_task

    with patch(
        "src.ui.pyside_ui.dialog_windows.main_window.main_window.asyncio.create_task",
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

    with patch("src.ui.pyside_ui.dialog_windows.main_window.main_window.asyncio.create_task") as mock_create_task:
        window.check_weather_score()

        mock_create_task.assert_not_called()
