from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol, cast

import panel as pn
import pytest
import respx
from httpx import HTTPStatusError, Response
from panel.io.callbacks import PeriodicCallback

import src.ui.panel_ui.time_panel.layout as module
from src.ui.panel_ui.time_panel.api import fetch_time
from src.ui.panel_ui.time_panel.clock_widget import ClockWidget
from src.ui.panel_ui.time_panel.layout import create_layout
from src.ui.shared.controller.clock_controller import ClockController
from src.ui.shared.helpers import format_datetime
from src.ui.shared.model.data_types import ClockHands

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


class SchedulerProtocol(Protocol):
    def add_periodic_callback(
        self,
        callback: Callable[[], None],
        period: int,
    ) -> PeriodicCallback: ...

    def on_session_destroyed(self, callback: Callable[..., None]) -> None: ...


class FakePeriodicCallback(PeriodicCallback):

    def __init__(self) -> None:
        pass

    def stop(self) -> None:
        pass


class FakeScheduler:
    def __init__(self) -> None:
        self.registered_cb: Callable[[], None] | None = None
        self.destroyed_cb: Callable[..., None] | None = None

    def add_periodic_callback(
        self,
        callback: Callable[[], None],
        period: int,
    ) -> PeriodicCallback:
        _ = period
        self.registered_cb = callback
        return FakePeriodicCallback()

    def on_session_destroyed(self, callback: Callable[..., None]) -> None:
        self.destroyed_cb = callback

    def tick(self) -> None:
        if self.registered_cb:
            self.registered_cb()


class FakeHooks:
    def __init__(
        self,
        fake_fetch: Callable[[], Coroutine[Any, Any, str]] | None = None,
    ) -> None:
        self._fake_fetch = fake_fetch
        self.onload_cb: Callable[[], None] | None = None

    def execute(self, coro_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        asyncio.run(coro_fn())

    def onload(self, callback: Callable[[], None]) -> None:
        self.onload_cb = callback


async def _async_return(value: str) -> str:
    await asyncio.sleep(0)
    return value


async def _async_raise(exc: Exception) -> str:
    await asyncio.sleep(0)
    raise exc


def _make_layout(
    fake_fetch: Callable[[], Coroutine[Any, Any, str]],
    *,
    trigger_onload: bool = True,
) -> tuple[pn.Column, FakeHooks, FakeScheduler]:
    hooks = FakeHooks(fake_fetch)
    scheduler = FakeScheduler()

    col = create_layout(
        hooks=hooks,
        scheduler=cast("SchedulerProtocol", scheduler),
        time_fetcher=fake_fetch,
    )

    if trigger_onload and hooks.onload_cb is not None:
        hooks.onload_cb()

    return col, hooks, scheduler


def _make_clock_widget() -> tuple[ClockWidget, FakeScheduler]:
    scheduler = FakeScheduler()
    widget = ClockWidget(
        size=300,
        scheduler=cast("SchedulerProtocol", scheduler),
    )
    return widget, scheduler


@pytest.mark.asyncio
async def test_fetch_time_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_HOST", "testserver")
    monkeypatch.setenv("API_PORT", "80")

    with respx.mock:
        respx.get("http://testserver:80/api/v1/time").mock(
            return_value=Response(200, json={"datetime": "2026-01-25T12:00:00Z"})
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


def test_on_click_success() -> None:
    async def fake_fetch_time() -> str:
        return await _async_return("2026-01-25T12:00:00Z")

    col, _hooks, _ = _make_layout(fake_fetch_time, trigger_onload=False)

    button = cast("pn.widgets.Button", col[2])
    time_display = cast("pn.pane.Markdown", col[3])

    assert time_display.object == "No data"

    button.clicks += 1

    assert time_display.object == "Server time: `2026-01-25T12:00:00Z`"


def test_on_click_error() -> None:
    async def fake_fetch_time() -> str:
        return await _async_raise(RuntimeError("boom"))

    col, _hooks, _ = _make_layout(fake_fetch_time, trigger_onload=False)

    button = cast("pn.widgets.Button", col[2])
    time_display = cast("pn.pane.Markdown", col[3])

    button.clicks += 1

    assert "Error:" in time_display.object
    assert "boom" in time_display.object


def test_on_click_sets_clock_datetime() -> None:
    async def fake_fetch_time() -> str:
        return await _async_return("2026-01-25T12:00:00+00:00")

    col, _, _ = _make_layout(fake_fetch_time, trigger_onload=False)

    clock_pane = cast("pn.pane.Bokeh", col[1])
    assert clock_pane.object.renderers is not None

    time_display = cast("pn.pane.Markdown", col[3])
    button = cast("pn.widgets.Button", col[2])

    button.clicks += 1

    assert "2026-01-25T12:00:00+00:00" in time_display.object


def test_onload_fetches_time_on_startup() -> None:
    async def fake_fetch_time() -> str:
        return await _async_return("2026-01-25T09:00:00+00:00")

    col, _hooks, _ = _make_layout(fake_fetch_time, trigger_onload=True)

    time_display = cast("pn.pane.Markdown", col[3])
    assert "2026-01-25T09:00:00+00:00" in time_display.object


def test_layout_structure() -> None:
    async def fake_fetch_time() -> str:
        return await _async_return("2026-01-25T12:00:00Z")

    col, _, _ = _make_layout(fake_fetch_time, trigger_onload=False)

    assert len(col) == 4
    assert isinstance(col[1], pn.pane.Bokeh)
    assert isinstance(col[2], pn.widgets.Button)
    assert isinstance(col[3], pn.pane.Markdown)


def test_clock_widget_uses_shared_clock_controller() -> None:
    widget, _ = _make_clock_widget()
    assert isinstance(widget._controller, ClockController)


def test_clock_widget_registers_periodic_callback() -> None:
    _, scheduler = _make_clock_widget()
    assert scheduler.registered_cb is not None


def test_clock_widget_registers_session_destroyed_callback() -> None:
    _, scheduler = _make_clock_widget()
    assert scheduler.destroyed_cb is not None


def test_clock_widget_set_current_datetime_resets_controller() -> None:
    widget, _ = _make_clock_widget()

    new_dt = datetime(2026, 1, 25, 12, 0, 0, tzinfo=UTC)
    widget.set_current_datetime(new_dt)

    assert widget._server_anchor == new_dt
    assert widget._controller._clock_hands == ClockHands(0.0, 0.0, 0.0)


def test_clock_widget_tick_updates_controller() -> None:
    widget, _ = _make_clock_widget()

    fixed_dt = datetime(2026, 1, 25, 12, 30, 45, tzinfo=UTC)
    widget.set_current_datetime(fixed_dt)
    widget._wall_anchor_mono -= 1.0

    widget._tick()

    hands = widget._controller._clock_hands
    assert hands.second != pytest.approx(0.0) or hands.minute != pytest.approx(0.0) or hands.hour != pytest.approx(0.0)


def test_clock_widget_tick_updates_bokeh_sources() -> None:
    widget, _ = _make_clock_widget()

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


def test_clock_widget_time_text_uses_format_datetime() -> None:
    widget, _ = _make_clock_widget()

    fixed_dt = datetime(2026, 1, 25, 8, 5, 3, 123000, tzinfo=UTC)
    widget.set_current_datetime(fixed_dt)

    widget._tick()

    displayed = widget._sources["time_text"].data["text"][0]
    expected = format_datetime(widget._current_datetime())

    assert re.match(r"\d{2}:\d{2}:\d{2}\.\d{3}", displayed), f"Unexpected format: {displayed}"
    assert displayed[:8] == expected[:8]


def test_clock_widget_current_datetime_advances() -> None:
    widget, _ = _make_clock_widget()

    base = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
    widget.set_current_datetime(base)
    widget._wall_anchor_mono -= 5.0

    computed = widget._current_datetime()
    delta = (computed - base).total_seconds()

    assert abs(delta - 5.0) < 0.1


def test_clock_widget_tick_via_scheduler() -> None:
    widget, scheduler = _make_clock_widget()

    fixed_dt = datetime(2026, 1, 25, 12, 0, 0, tzinfo=UTC)
    widget.set_current_datetime(fixed_dt)
    widget._wall_anchor_mono -= 2.0

    scheduler.tick()

    hands = widget._controller._clock_hands
    assert hands.second != pytest.approx(0.0) or hands.minute != pytest.approx(0.0) or hands.hour != pytest.approx(0.0)


def test_no_inline_pid_classes() -> None:
    assert not hasattr(module, "PID"), "time_panel should not define its own PID class"
    assert not hasattr(
        module,
        "PIDMovement",
    ), "time_panel should not define its own PIDMovement"
