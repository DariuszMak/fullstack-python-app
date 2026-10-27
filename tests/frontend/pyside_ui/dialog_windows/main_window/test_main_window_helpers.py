from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6.QtWidgets import QLabel

from src.backend.api.models.weather_score_response import BestScoreResponse, PlaceBestScoreRecord
from src.frontend.pyside_ui.dialog_windows.main_window.helpers import clear_layout, render_weather_score
from src.frontend.pyside_ui.dialog_windows.main_window.main_window import MainWindow
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score_state import WeatherScoreState
from src.frontend.pyside_ui.widgets.weather_score_card import WeatherScoreCard

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


async def run_check(window: MainWindow) -> None:
    window.check_weather_score()
    task = window._weather_score_task
    assert task is not None
    await task


@pytest.mark.asyncio
async def test_check_weather_score_renders_cards_on_success(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._httpx_client.fetch_weather_score = AsyncMock(return_value=make_response())  # type: ignore[method-assign]

    await run_check(window)

    assert len(cards_in_layout(window)) == 2


@pytest.mark.asyncio
async def test_check_weather_score_orders_cards_by_score_descending(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._httpx_client.fetch_weather_score = AsyncMock(return_value=make_response())  # type: ignore[method-assign]

    await run_check(window)

    cards = cards_in_layout(window)
    assert cards[0].name == "Krakow"
    assert cards[1].name == "Wroclaw"


def testrender_weather_score_creates_one_card_per_place(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    render_weather_score(window._ui.weatherScoreContainerLayout, make_response())

    assert len(cards_in_layout(window)) == 2


def testrender_weather_score_sorts_by_score_descending(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    render_weather_score(window._ui.weatherScoreContainerLayout, make_response())

    cards = cards_in_layout(window)
    assert cards[0].name == "Krakow"
    assert cards[1].name == "Wroclaw"


def testrender_weather_score_assigns_rank_labels(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    render_weather_score(window._ui.weatherScoreContainerLayout, make_response())

    cards = cards_in_layout(window)
    assert cards[0]._rank_label.text() == "#1"
    assert cards[1]._rank_label.text() == "#2"


def testrender_weather_score_clears_previous_cards(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    render_weather_score(window._ui.weatherScoreContainerLayout, make_response())
    assert len(cards_in_layout(window)) == 2

    smaller_response = make_response()
    smaller_response.results = smaller_response.results[:1]

    render_weather_score(window._ui.weatherScoreContainerLayout, smaller_response)

    assert len(cards_in_layout(window)) == 1


def testrender_weather_score_with_no_results_shows_empty_message(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    empty_response = make_response()
    empty_response.results = []

    render_weather_score(window._ui.weatherScoreContainerLayout, empty_response)

    assert len(cards_in_layout(window)) == 0
    assert any("No matching places" in text for text in labels_text(window))


def test_clear_layout_removes_all_items(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    render_weather_score(window._ui.weatherScoreContainerLayout, make_response())
    layout = window._ui.weatherScoreContainerLayout
    assert layout.count() > 0

    clear_layout(layout)

    assert layout.count() == 0


def test_viewmodel_error_state_clears_cards_and_shows_message(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    render_weather_score(window._ui.weatherScoreContainerLayout, make_response())
    assert len(cards_in_layout(window)) == 2

    window._viewmodel.state_changed.emit(WeatherScoreState(error="test_message"))

    assert len(cards_in_layout(window)) == 0
    assert any("Failed to fetch weather score: test_message" in text for text in labels_text(window))


def test_viewmodel_loading_state_clears_cards_and_shows_message(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    render_weather_score(window._ui.weatherScoreContainerLayout, make_response())
    assert len(cards_in_layout(window)) == 2

    window._viewmodel.state_changed.emit(WeatherScoreState(is_loading=True))

    assert len(cards_in_layout(window)) == 0
    assert any("Fetching weather score..." in text for text in labels_text(window))


@pytest.mark.asyncio
async def test_check_weather_score_shows_info_message_while_fetching(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    render_weather_score(window._ui.weatherScoreContainerLayout, make_response())
    assert len(cards_in_layout(window)) == 2

    observed_card_counts: list[int] = []
    observed_texts: list[list[str]] = []

    async def fetch_side_effect(*args: object, **kwargs: object) -> BestScoreResponse:
        await asyncio.sleep(0)
        observed_card_counts.append(len(cards_in_layout(window)))
        observed_texts.append(labels_text(window))
        return make_response()

    window._httpx_client.fetch_weather_score = AsyncMock(side_effect=fetch_side_effect)  # type: ignore[method-assign]

    await run_check(window)

    assert observed_card_counts == [0]
    assert any("Fetching weather score..." in text for text in observed_texts[0])
    assert len(cards_in_layout(window)) == 2


@pytest.mark.asyncio
async def test_check_weather_score_shows_error_on_failure(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._httpx_client.fetch_weather_score = AsyncMock(side_effect=RuntimeError("test_message"))  # type: ignore[method-assign]

    await run_check(window)

    assert len(cards_in_layout(window)) == 0
    assert any("Failed to fetch weather score: test_message" in text for text in labels_text(window))


@pytest.mark.asyncio
async def test_check_weather_score_shows_exception_type_when_error_message_is_empty(
    qtbot: QtBot,
) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._httpx_client.fetch_weather_score = AsyncMock(side_effect=TimeoutError())  # type: ignore[method-assign]

    await run_check(window)

    assert any("Failed to fetch weather score: TimeoutError" in text for text in labels_text(window))


@pytest.mark.asyncio
async def test_check_weather_score_replaces_error_with_cards_on_retry(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._httpx_client.fetch_weather_score = AsyncMock(side_effect=RuntimeError("boom"))  # type: ignore[method-assign]
    await run_check(window)
    assert any("boom" in text for text in labels_text(window))

    window._httpx_client.fetch_weather_score = AsyncMock(return_value=make_response())  # type: ignore[method-assign]
    await run_check(window)

    assert len(cards_in_layout(window)) == 2
    assert not any("boom" in text for text in labels_text(window))


@pytest.mark.asyncio
async def test_check_weather_score_toggles_button_while_fetching(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    observed: list[tuple[bool, str]] = []

    def fetch_side_effect(*args: object, **kwargs: object) -> BestScoreResponse:
        button = window._ui.checkWeatherScoreButton
        observed.append((button.isEnabled(), button.text()))
        return make_response()

    window._httpx_client.fetch_weather_score = AsyncMock(side_effect=fetch_side_effect)  # type: ignore[method-assign]

    await run_check(window)

    assert observed == [(False, "Fetching...")]
    assert window._ui.checkWeatherScoreButton.isEnabled() is True
    assert window._ui.checkWeatherScoreButton.text() == "Get weather score"


@pytest.mark.asyncio
async def test_check_weather_score_reenables_button_after_failure(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._httpx_client.fetch_weather_score = AsyncMock(side_effect=RuntimeError("boom"))  # type: ignore[method-assign]

    await run_check(window)

    assert window._ui.checkWeatherScoreButton.isEnabled() is True
    assert window._ui.checkWeatherScoreButton.text() == "Get weather score"


@pytest.mark.asyncio
async def test_check_weather_score_ignores_call_while_task_is_running(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    release = asyncio.Event()

    async def fetch_side_effect(*args: object, **kwargs: object) -> BestScoreResponse:
        await release.wait()
        return make_response()

    mock = AsyncMock(side_effect=fetch_side_effect)
    window._httpx_client.fetch_weather_score = mock  # type: ignore[method-assign]

    window.check_weather_score()
    first_task = window._weather_score_task
    await asyncio.sleep(0)
    window.check_weather_score()

    assert window._weather_score_task is first_task

    release.set()
    assert first_task is not None
    await first_task

    assert mock.call_count == 1


def test_check_weather_score_without_running_loop_does_nothing(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    mock = AsyncMock(return_value=make_response())
    window._httpx_client.fetch_weather_score = mock  # type: ignore[method-assign]

    window.check_weather_score()

    mock.assert_not_called()


def test_fetch_weather_score_initial_delegates_to_check_weather_score(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window.check_weather_score = MagicMock()  # type: ignore[method-assign]

    window._fetch_weather_score_initial()

    window.check_weather_score.assert_called_once_with()


def test_on_loading_changed_updates_button(qtbot: QtBot) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)

    window._on_loading_changed(True)
    assert window._ui.checkWeatherScoreButton.isEnabled() is False
    assert window._ui.checkWeatherScoreButton.text() == "Fetching..."

    window._on_loading_changed(False)
    assert window._ui.checkWeatherScoreButton.isEnabled() is True
    assert window._ui.checkWeatherScoreButton.text() == "Get weather score"
