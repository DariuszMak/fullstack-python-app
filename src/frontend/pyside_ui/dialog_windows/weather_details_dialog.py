from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import pyqtgraph as pg
import structlog
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.frontend.pyside_ui.dialog_windows.draggable_window.draggable_dialog import DraggableDialog
from src.frontend.pyside_ui.forms.moc_weather_details_dialog import Ui_Dialog
from src.helpers.config.config import Config
from src.helpers.style_loader import StyleLoader
from PySide6.QtCore import QEvent, Qt, Signal, Slot
from shiboken6 import isValid

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent, QShowEvent

    from src.backend.api.models.weather_info_response import HourlyRecord, WeatherInfoResponse
    from src.backend.api.models.weather_score_response import PlaceBestScoreRecord

logger = structlog.get_logger(__name__)


class WeatherDetailsDialog(DraggableDialog):
    weather_info_ready = Signal(object)
    def __init__(self, place: PlaceBestScoreRecord, rank: int | None = None, parent: QWidget | None = None) -> None:

        super().__init__()
        self._place = place
        self._values: dict[str, QLabel] = {}
        self._plot_widget: pg.PlotWidget | None = None
        self._weather_info_task: asyncio.Task[None] | None = None
        self.weather_info_ready.connect(self._update_plot, Qt.ConnectionType.QueuedConnection)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)
        self._build_ui(rank)
        StyleLoader.style_window(self)  

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._ui.btn_close.clicked.connect(self.close)
        StyleLoader.center_window(self, parent)

        self.ensurePolished()
        self.adjustSize()

        logger.debug("weather_details_dialog_initialized", parent=type(parent).__name__ if parent else None)

    @property
    def place(self) -> PlaceBestScoreRecord:
        return self._place

    def value(self, field: str) -> str:
        return self._values[field].text()

    def _build_ui(self, rank: int | None) -> None:
        outer_layout = self._ui.formLayout

        self._container = QFrame(self)
        self._container.setObjectName("weatherDetailsFrame")
        outer_layout.addWidget(self._container)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(20, 10, 20, 20)
        container_layout.setSpacing(14)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        self._title_label = QLabel(self._place.name, self._container)
        self._title_label.setObjectName("label_title_bar_top")
        title_font = self._title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 4)
        self._title_label.setFont(title_font)

        title_layout.addWidget(self._title_label, 1)
        container_layout.addLayout(title_layout)

        separator = QFrame(self._container)
        separator.setFixedHeight(1)
        container_layout.addWidget(separator)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        rows = (
            ("name", "Name", self._place.name),
            ("rank", "Rank", f"#{rank}" if rank is not None else "-"),
            ("key", "Key", self._place.key),
            ("latitude", "Latitude", f"{self._place.latitude:.4f}"),
            ("longitude", "Longitude", f"{self._place.longitude:.4f}"),
            ("timezone", "Timezone", self._place.timezone),
            ("score", "Score", f"{self._place.score:.2f}"),
            ("calculated_score", "Calculated score", f"{self._place.percentage_score:.2f}"),
        )

        for row, (field, caption, text) in enumerate(rows):
            caption_label = QLabel(caption, self._container)
            value_label = QLabel(text, self._container)
            value_label.setWordWrap(True)
            grid.addWidget(caption_label, row, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(value_label, row, 1)
            self._values[field] = value_label

        container_layout.addLayout(grid)

        self._plot_widget = pg.PlotWidget(axisItems={"bottom": pg.DateAxisItem(utcOffset=0)})
        self._plot_widget.setLabel("left", "Temperature (\u00b0C)")
        self._plot_widget.setLabel("bottom", "Date")
        self._plot_widget.setTitle("Hourly Forecast")
        self._plot_widget.addLegend()
        container_layout.addWidget(self._plot_widget, 1)

        container_layout.addStretch(1)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._fetch_weather_info()

    def _fetch_weather_info(self) -> None:
        if self._weather_info_task is not None and not self._weather_info_task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._weather_info_task = loop.create_task(self._do_fetch_weather_info())

    def _cancel_fetch(self) -> None:
        if self._weather_info_task is not None and not self._weather_info_task.done():
            self._weather_info_task.cancel()

    async def _do_fetch_weather_info(self) -> None:
        from src.frontend.shared.client.httpx_client import HttpxClient

        config = Config()
        client = HttpxClient(config.api_base_url)

        try:
            response = await client.fetch_weather_info(
                latitude=self._place.latitude,
                longitude=self._place.longitude,
                timezone=self._place.timezone,
                forecast_days=3,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("weather_info_plot_failed")
            return

        if isValid(self):
            self.weather_info_ready.emit(response)

    @Slot(object)
    def _update_plot(self, response: WeatherInfoResponse) -> None:
        if self._plot_widget is None or not isValid(self._plot_widget):
            return

        hourly: list[HourlyRecord] = response.hourly
        if not hourly:
            return

        dates = np.array([self._to_epoch(r.date) for r in hourly], dtype=float)
        temps = np.array([r.temperature_2m for r in hourly], dtype=float)
        apparent_temps = np.array([r.apparent_temperature for r in hourly], dtype=float)

        self._plot_widget.clear()
        self._plot_widget.plot(dates, temps, pen="r", name="Temperature")
        self._plot_widget.plot(dates, apparent_temps, pen="b", name="Apparent Temp")
        self._plot_widget.showGrid(x=True, y=True)

    def _to_epoch(self, value: object) -> float:
        """Convert a timestamp to epoch seconds (pyqtgraph needs numbers, not datetimes).

        The value is shifted to the place's local wall-clock time, so the axis
        (DateAxisItem with utcOffset=0) shows local time of the forecast location.
        """
        ts = pd.Timestamp(value)
        if ts.tzinfo is not None:
            with contextlib.suppress(Exception):
                ts = ts.tz_convert(self._place.timezone)
            ts = ts.tz_localize(None)
        return float(ts.timestamp())

    def changeEvent(self, event: QEvent) -> None:  # ruff: ignore[invalid-function-name]
        if event.type() == QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)  # type: ignore[no-untyped-call]
            logger.debug("dialog_language_changed")
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # ruff: ignore[invalid-function-name]
        logger.info("weather_details_dialog_closed", place=self._place.key)
        self._cancel_fetch()
        super().closeEvent(event)
