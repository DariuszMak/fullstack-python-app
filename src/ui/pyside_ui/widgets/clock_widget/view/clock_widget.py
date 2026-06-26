from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from src.ui.pyside_ui.widgets.clock_widget.view.painter import Painter
from src.ui.pyside_ui.widgets.clock_widget.view.tick_events import TickEventSubject
from src.ui.shared.controller.clock_controller import ClockController
from src.ui.shared.helpers import convert_clock_pid_to_cartesian

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintEvent


class ClockWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._duration = 15

        self._tick_subject = TickEventSubject()
        self._tick_subject.subscribe(self)

        self._timer: QTimer = QTimer(self)
        self._timer.timeout.connect(self._tick_subject.notify)
        self._timer.start(self._duration)
        self._server_anchor: datetime = datetime.now().astimezone()
        self._wall_anchor_mono: float = time.monotonic()

        self._current_datetime: datetime = self._server_anchor
        self._controller = ClockController(self._current_datetime)

    def on_tick(self) -> None:
        self._current_datetime = self._server_anchor + timedelta(seconds=time.monotonic() - self._wall_anchor_mono)
        self._controller.update(self._current_datetime)
        self.update()

    def set_current_datetime(self, dt: datetime) -> None:
        self._server_anchor = dt
        self._wall_anchor_mono = time.monotonic()
        self.reset()

    def reset(self) -> None:
        self._controller.reset(self._current_datetime)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802, ARG002
        painter = Painter(self)

        center, radius, font_size = painter.paint_clock_face(self.rect, self.palette)
        hands_position = convert_clock_pid_to_cartesian(self._controller._clock_hands, center, radius)

        painter.paint_hands(center, hands_position)
        painter.paint_current_time(self._current_datetime, center, radius, font_size)
