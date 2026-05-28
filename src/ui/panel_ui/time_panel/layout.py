from __future__ import annotations

from collections.abc import Callable, Coroutine
from datetime import datetime
from typing import Any, Protocol

import panel as pn
import structlog

from src.ui.panel_ui.time_panel.api import fetch_time
from src.ui.panel_ui.time_panel.clock_widget import ClockWidget, PanelStateScheduler, PeriodicScheduler

logger = structlog.get_logger(__name__)


class LayoutHooks(Protocol):
    """Lifecycle hooks needed by create_layout.

    Separating these from ClockWidget's scheduler lets each be faked
    independently in tests without touching pn.state at all.
    """

    def execute(self, coro_fn: Callable[[], Coroutine[Any, Any, None]]) -> None: ...

    def onload(self, callback: Callable[[], None]) -> None: ...


class PanelStateHooks:
    """Production adapter — thin wrapper around pn.state."""

    def execute(self, coro_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        pn.state.execute(coro_fn)

    def onload(self, callback: Callable[[], None]) -> None:
        pn.state.onload(callback)


def create_layout(
    hooks: LayoutHooks | None = None,
    scheduler: PeriodicScheduler | None = None,
) -> pn.Column:
    """Build the Panel layout.

    Parameters
    ----------
    hooks:
        Lifecycle hooks (execute, onload).  Defaults to the real pn.state
        adapters; pass a test double in tests.
    scheduler:
        Periodic-callback scheduler for ClockWidget.  Same default rule.
    """
    _hooks = hooks or PanelStateHooks()
    _scheduler = scheduler or PanelStateScheduler()

    logger.info("creating_layout")
    clock = ClockWidget(size=300, scheduler=_scheduler)

    time_display: pn.pane.Markdown = pn.pane.Markdown("No data", sizing_mode="stretch_width")  # type: ignore

    button: pn.widgets.Button = pn.widgets.Button(
        label="Fetch time from API",
        color="primary",
    )  # type: ignore

    async def _fetch() -> None:
        log = logger.bind(action="fetch_server_time")
        try:
            time_display.object = "Loading..."
            log.info("request_started")

            dt_str = await fetch_time()
            dt = datetime.fromisoformat(dt_str)

            clock.set_current_datetime(dt)
            time_display.object = f"Server time: `{dt_str}`"

            log.info("request_successful", server_time=dt_str)
        except Exception as exc:
            log.exception("request_failed", error=str(exc))
            time_display.object = f"Error: `{exc}`"

    def on_click(_: object) -> None:
        logger.debug("button_clicked")
        _hooks.execute(_fetch)

    def _on_load() -> None:
        logger.info("application_payload_loaded")
        _hooks.execute(_fetch)

    button.on_click(on_click)
    _hooks.onload(_on_load)

    return pn.Column(
        "# Server Time",
        clock.panel(),
        button,
        time_display,
        width=400,
    )