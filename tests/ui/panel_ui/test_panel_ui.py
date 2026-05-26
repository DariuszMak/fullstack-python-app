import asyncio
import re
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock, patch

import panel as pn
import pytest
import respx
from httpx import HTTPStatusError, Response

import src.ui.panel_ui.time_panel.layout as module
from src.ui.panel_ui.time_panel import layout
from src.ui.panel_ui.time_panel.api import fetch_time
from src.ui.panel_ui.time_panel.clock_widget import ClockWidget
from src.ui.shared.controller.clock_controller import ClockController
from src.ui.shared.helpers import format_datetime
from src.ui.shared.model.data_types import ClockHands


@pytest.mark.asyncio
async def test_fetch_time_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_HOST", "testserver")
    monkeypatch.setenv("API_PORT", "80")

    with respx.mock:
        respx.get("http://testserver:80/api/v1/time").mock(
            return_value=Response(
                200,
                json={"datetime": "2026-01-25T12:00:00Z"},
            )
        )

        result = await fetch_time()

    assert result == "2026-01-25T12:00:00Z"


@pytest.mark.asyncio
async def test_fetch_time_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_HOST", "testserver")
    monkeypatch.setenv("API_PORT", "80")

    with respx.mock:
        respx.get("http://testserver:80/api/v1/time").mock(return_value=Response(500))

        with pytest.raises(HTTPStatusError):
            await fetch_time()


def _make_layout(
    monkeypatch: pytest.MonkeyPatch,
    fake_fetch: Callable[[], Coroutine[None, None, str]],
) -> pn.Column:

    def immediate_execute(fn: Callable[[], Coroutine[None, None, None]]) -> None:
        asyncio.run(fn())

    monkeypatch.setattr(layout, "fetch_time", fake_fetch)
    monkeypatch.setattr(pn.state, "execute", immediate_execute)
    monkeypatch.setattr(pn.state, "onload", lambda _: None)

    with patch.object(pn.state, "add_periodic_callback", return_value=MagicMock()):
        return layout.create_layout()


def test_on_click_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_time() -> str:  # noqa: RUF029
        return "2026-01-25T12:00:00Z"

    col = _make_layout(monkeypatch, fake_fetch_time)

    button = cast("pn.widgets.Button", col[2])
    time_display = cast("pn.pane.Markdown", col[3])

    assert time_display.object == "No data"

    button.clicks += 1

    assert time_display.object == "Server time: `2026-01-25T12:00:00Z`"


def test_on_click_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_time() -> str:  # noqa: RUF029
        raise RuntimeError("boom")

    col = _make_layout(monkeypatch, fake_fetch_time)

    button = cast("pn.widgets.Button", col[2])
    time_display = cast("pn.pane.Markdown", col[3])

    button.clicks += 1

    assert "Error:" in time_display.object
    assert "boom" in time_display.object


def test_on_click_sets_clock_datetime(monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[datetime] = []

    async def fake_fetch_time() -> str:  # noqa: RUF029
        return "2026-01-25T12:00:00+00:00"

    original_init = ClockWidget.__init__

    def patched_init(self: ClockWidget, size: int = 300) -> None:
        original_init(self, size)
        original_set = self.set_current_datetime

        def capturing_set(dt: datetime) -> None:
            received.append(dt)
            original_set(dt)

        self.set_current_datetime = capturing_set  # type: ignore[method-assign]

    monkeypatch.setattr(ClockWidget, "__init__", patched_init)

    col = _make_layout(monkeypatch, fake_fetch_time)
    button = cast("pn.widgets.Button", col[2])

    button.clicks += 1

    assert len(received) == 1
    assert received[0] == datetime(2026, 1, 25, 12, 0, 0, tzinfo=UTC)


def test_layout_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_time() -> str:  # noqa: RUF029
        return "2026-01-25T12:00:00Z"

    col = _make_layout(monkeypatch, fake_fetch_time)

    assert len(col) == 4
    assert isinstance(col[1], pn.pane.Bokeh)
    assert isinstance(col[2], pn.widgets.Button)
    assert isinstance(col[3], pn.pane.Markdown)


def _make_clock_widget(monkeypatch: pytest.MonkeyPatch) -> ClockWidget:
    with patch.object(pn.state, "add_periodic_callback", return_value=MagicMock()):
        return ClockWidget(size=300)


def test_clock_widget_uses_shared_clock_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    widget = _make_clock_widget(monkeypatch)
    assert isinstance(widget._controller, ClockController)


def test_clock_widget_set_current_datetime_resets_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    widget = _make_clock_widget(monkeypatch)

    new_dt = datetime(2026, 1, 25, 12, 0, 0, tzinfo=UTC)
    widget.set_current_datetime(new_dt)

    assert widget._server_anchor == new_dt
    assert widget._controller._clock_hands == ClockHands(0.0, 0.0, 0.0)


def test_clock_widget_tick_updates_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    widget = _make_clock_widget(monkeypatch)

    fixed_dt = datetime(2026, 1, 25, 12, 30, 45, tzinfo=UTC)
    widget.set_current_datetime(fixed_dt)

    widget._wall_anchor_mono -= 1.0

    widget._tick()

    hands = widget._controller._clock_hands
    assert hands.second != pytest.approx(0.0) or hands.minute != pytest.approx(0.0) or hands.hour != pytest.approx(0.0)


def test_clock_widget_tick_updates_bokeh_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    widget = _make_clock_widget(monkeypatch)

    fixed_dt = datetime(2026, 1, 25, 3, 0, 0, tzinfo=UTC)
    widget.set_current_datetime(fixed_dt)

    widget._wall_anchor_mono -= 60.0

    widget._tick()

    for key in ("hour", "minute", "second"):
        xs = widget._sources[key].data["x"]
        ys = widget._sources[key].data["y"]
        assert len(xs) == 2
        assert len(ys) == 2
        assert not (xs[1] == pytest.approx(0.0) and ys[1] == pytest.approx(0.0)), f"{key} hand tip is still at origin"


def test_clock_widget_time_text_uses_format_datetime(monkeypatch: pytest.MonkeyPatch) -> None:
    widget = _make_clock_widget(monkeypatch)

    fixed_dt = datetime(2026, 1, 25, 8, 5, 3, 123000, tzinfo=UTC)
    widget.set_current_datetime(fixed_dt)

    widget._tick()

    displayed = widget._sources["time_text"].data["text"][0]
    expected = format_datetime(widget._current_datetime())

    assert re.match(r"\d{2}:\d{2}:\d{2}\.\d{3}", displayed), f"Unexpected format: {displayed}"
    assert displayed[:8] == expected[:8]


def test_clock_widget_current_datetime_advances(monkeypatch: pytest.MonkeyPatch) -> None:
    widget = _make_clock_widget(monkeypatch)

    base = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
    widget.set_current_datetime(base)

    widget._wall_anchor_mono -= 5.0

    computed = widget._current_datetime()
    delta = (computed - base).total_seconds()

    assert abs(delta - 5.0) < 0.1


def test_no_inline_pid_classes(monkeypatch: pytest.MonkeyPatch) -> None:
    assert not hasattr(module, "PID"), "time_panel should not define its own PID class"
    assert not hasattr(module, "PIDMovement"), "time_panel should not define its own PIDMovement"
