from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

from PySide6.QtWidgets import QLabel

from src.backend.api.models.weather_score_response import BestScoreResponse, PlaceBestScoreRecord
from src.ui.pyside_ui.dialog_windows.main_window.helpers import _clear_layout, _render_weather_score
from src.ui.pyside_ui.dialog_windows.main_window.main_window import MainWindow
from src.ui.pyside_ui.widgets.weather_score_card import WeatherScoreCard

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
                score=0.5,
            ),
            PlaceBestScoreRecord(
                key="krakow",
                name="Krakow",
                latitude=50.0,
                longitude=19.9,
                timezone="Europe/Warsaw",
                score=0.8,
            ),
        ],
        min_threshold=20.0,
        max_threshold=25.0,
        penalize_rain=True,
        start_day=0,
    )


def cards_in_layout(window: MainWindow) -> list[WeatherScoreCard]:
    layout = window._ui.weatherScoreContainerLayout
    cards: list[WeatherScoreCard] = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is None:
            continue
        widget = item.widget()
        if isinstance(widget, WeatherScoreCard):
            cards.append(widget)
    return cards


def labels_text(window: MainWindow) -> list[str]:
    layout = window._ui.weatherScoreContainerLayout
    texts: list[str] = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item is None:
            continue
        widget = item.widget()
        if isinstance(widget, QLabel):
            texts.append(widget.text())
    return texts


def test_render_weather_score_creates_one_card_per_place(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    _render_weather_score(window._ui.weatherScoreContainerLayout, make_response())

    assert len(cards_in_layout(window)) == 2


def test_render_weather_score_sorts_by_score_descending(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    _render_weather_score(window._ui.weatherScoreContainerLayout, make_response())

    cards = cards_in_layout(window)
    assert cards[0].name == "Krakow"
    assert cards[1].name == "Wroclaw"


def test_render_weather_score_assigns_rank_labels(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    _render_weather_score(window._ui.weatherScoreContainerLayout, make_response())

    cards = cards_in_layout(window)
    assert cards[0]._rank_label.text() == "#1"
    assert cards[1]._rank_label.text() == "#2"


def test_render_weather_score_clears_previous_cards(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    _render_weather_score(window._ui.weatherScoreContainerLayout, make_response())
    assert len(cards_in_layout(window)) == 2

    smaller_response = make_response()
    smaller_response.results = smaller_response.results[:1]

    _render_weather_score(window._ui.weatherScoreContainerLayout, smaller_response)

    assert len(cards_in_layout(window)) == 1


def test_render_weather_score_with_no_results_shows_empty_message(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    empty_response = make_response()
    empty_response.results = []

    _render_weather_score(window._ui.weatherScoreContainerLayout, empty_response)

    assert len(cards_in_layout(window)) == 0
    assert any("No matching places" in text for text in labels_text(window))


def test_show_weather_score_error_clears_cards_and_shows_message(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    _render_weather_score(window._ui.weatherScoreContainerLayout, make_response())
    assert len(cards_in_layout(window)) == 2

    window._show_weather_score_error("test_message")

    assert len(cards_in_layout(window)) == 0
    assert any("Failed to fetch weather score: test_message" in text for text in labels_text(window))


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


def test_fetch_weather_score_renders_cards_on_success(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    response = make_response()
    window._time_client.fetch_weather_score = AsyncMock(return_value=response)  # type: ignore[method-assign]

    asyncio.run(window._fetch_weather_score())

    assert len(cards_in_layout(window)) == 2


def test_fetch_weather_score_shows_error_on_failure(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._time_client.fetch_weather_score = AsyncMock(side_effect=RuntimeError("test_message"))  # type: ignore[method-assign]

    asyncio.run(window._fetch_weather_score())

    assert any("Failed to fetch weather score: test_message" in text for text in labels_text(window))


def test_clear_layout_removes_all_items(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    _render_weather_score(window._ui.weatherScoreContainerLayout, make_response())
    layout = window._ui.weatherScoreContainerLayout
    assert layout.count() > 0

    _clear_layout(layout)

    assert layout.count() == 0
