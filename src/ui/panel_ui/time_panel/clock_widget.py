from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol

import panel as pn
import structlog

from src.ui.panel_ui.settings import TICK_MS
from src.ui.panel_ui.time_panel.clock_figure import build_clock_figure, hand_endpoint
from src.ui.shared.controller.clock_controller import ClockController
from src.ui.shared.helpers import clock_hands_in_radians, format_datetime

if TYPE_CHECKING:
    from collections.abc import Callable

    from panel.io.callbacks import PeriodicCallback

logger = structlog.get_logger(__name__)


class PeriodicScheduler(Protocol):
    """Minimal interface for registering a repeating callback.

    Keeping this as a Protocol (not an ABC) means the real pn.state and any
    test double both satisfy it without inheriting anything from Panel.
    """

    def add_periodic_callback(
        self,
        callback: Callable[[], None],
        period: int,
    ) -> PeriodicCallback: ...

    def on_session_destroyed(self, callback: Callable[..., None]) -> None: ...


class PanelStateScheduler:
    """Production adapter — thin wrapper around pn.state."""

    def add_periodic_callback(
        self,
        callback: Callable[[], None],
        period: int,
    ) -> PeriodicCallback:
        return pn.state.add_periodic_callback(callback, period=period)

    def on_session_destroyed(self, callback: Callable[..., None]) -> None:
        pn.state.on_session_destroyed(callback)


class ClockWidget:
    def __init__(
        self,
        size: int = 300,
        scheduler: PeriodicScheduler | None = None,
    ) -> None:
        self._server_anchor: datetime = datetime.now().astimezone()
        self._wall_anchor_mono: float = time.monotonic()

        self._controller = ClockController(self._server_anchor)
        self._scheduler = scheduler or PanelStateScheduler()

        self._fig, self._sources = build_clock_figure(size)
        self._pane: pn.pane.Bokeh = pn.pane.Bokeh(self._fig, sizing_mode="fixed")  # type: ignore

        logger.info("initializing_clock_widget", size=size, tick_ms=TICK_MS)
        self._cb: PeriodicCallback = self._scheduler.add_periodic_callback(self._tick, period=TICK_MS)

        self._scheduler.on_session_destroyed(self._on_session_destroyed)

    def _on_session_destroyed(self, _session_context: object) -> None:
        logger.info("session_destroyed_stopping_clock")
        self.stop()

    def panel(self) -> pn.pane.Bokeh:
        return self._pane

    def set_current_datetime(self, dt: datetime) -> None:
        logger.info("resetting_clock_anchor", new_time=dt.isoformat())
        self._server_anchor = dt
        self._wall_anchor_mono = time.monotonic()
        self._controller.reset(dt)

    def stop(self) -> None:
        if self._cb is not None:
            try:
                logger.debug("stopping_periodic_callback")
                self._cb.stop()  # type: ignore[no-untyped-call]
            except Exception as e:
                logger.exception("failed_to_stop_callback", error=str(e))

    def _current_datetime(self) -> datetime:
        elapsed = time.monotonic() - self._wall_anchor_mono
        return self._server_anchor + timedelta(seconds=elapsed)

    def _tick(self) -> None:
        now = self._current_datetime()
        self._controller.update(now)

        sec_rad, min_rad, hour_rad = clock_hands_in_radians(self._controller._clock_hands)

        cx, cy, r = 0.0, 0.0, 1.0

        ex_h, ey_h = hand_endpoint(cx, cy, r * 0.5, hour_rad)
        ex_m, ey_m = hand_endpoint(cx, cy, r * 0.7, min_rad)
        ex_s, ey_s = hand_endpoint(cx, cy, r * 0.9, sec_rad)

        self._sources["hour"].data = {"x": [cx, ex_h], "y": [cy, ey_h]}
        self._sources["minute"].data = {"x": [cx, ex_m], "y": [cy, ey_m]}
        self._sources["second"].data = {"x": [cx, ex_s], "y": [cy, ey_s]}

        formatted_time = format_datetime(now)
        self._sources["time_text"].data = {
            "x": [0.0],
            "y": [-0.55],
            "text": [formatted_time],
        }
