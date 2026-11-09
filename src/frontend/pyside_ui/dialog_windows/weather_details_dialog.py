from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pandas as pd
import pyqtgraph as pg
import structlog
from PySide6.QtCore import QEvent, Qt, Signal, Slot
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from shiboken6 import isValid

from src.frontend.pyside_ui.dialog_windows.draggable_window.draggable_dialog import DraggableDialog
from src.frontend.pyside_ui.forms.moc_weather_details_dialog import Ui_Dialog
from src.frontend.shared.client.httpx_client import HttpxClient
from src.helpers.config.config import Config
from src.helpers.style_loader import StyleLoader

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent, QShowEvent

    from src.backend.api.models.weather_info_response import HourlyRecord, WeatherInfoResponse
    from src.backend.api.models.weather_score_response import PlaceBestScoreRecord

logger = structlog.get_logger(__name__)

HOUR_SECONDS: float = 3600.0
DAY_SECONDS = 86400.0
BAR_WIDTH_RATIO: float = 0.8
PRECIPITATION_COLOR: tuple[int, int, int] = (46, 204, 113)
PRECIPITATION_BAR_ALPHA: int = 170
PRECIPITATION_HEADROOM: float = 1.2
MIN_PRECIPITATION_AXIS_MAX: float = 1.0


class CustomDateAxisItem(pg.DateAxisItem):
    def tickValues(self, minVal: float, maxVal: float, size: float) -> list[tuple[float, list[float]]]:
        span = maxVal - minVal

        if span <= 3 * DAY_SECONDS:
            return super().tickValues(minVal, maxVal, size)

        cal = self.generateCalendar(minVal, maxVal)
        days = [float(ts.timestamp()) for ts in cal]

        ticks = []
        for d in days:
            if minVal <= d <= maxVal:
                ticks.append(d)

        return [(DAY_SECONDS, ticks), (DAY_SECONDS * 7, [])]


class WeatherDetailsDialog(DraggableDialog):
    weather_info_ready = Signal(object)

    def __init__(
        self,
        place: PlaceBestScoreRecord,
        rank: int | None = None,
        parent: QWidget | None = None,
        forecast_days: int = 3,
        start_day: int = 0,
    ) -> None:

        super().__init__()
        self._place = place
        self._forecast_days = forecast_days
        self._start_day = start_day
        self._values: dict[str, QLabel] = {}
        self._plot_widget: pg.PlotWidget | None = None
        self._precip_view: pg.ViewBox | None = None
        self._precipitation_bars: pg.BarGraphItem | None = None
        self._weather_info_task: asyncio.Task[None] | None = None
        self.weather_info_ready.connect(self._update_plot, Qt.ConnectionType.QueuedConnection)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._build_ui(rank)
        StyleLoader.style_window(self)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._ui.btn_close.clicked.connect(self.close)
        StyleLoader.center_window(self, parent)

        logger.debug(
            "weather_details_dialog_initialized",
            parent=type(parent).__name__ if parent else None,
            forecast_days=self._forecast_days,
            start_day=self._start_day,
        )

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

        self._plot_widget = pg.PlotWidget(axisItems={"bottom": CustomDateAxisItem(utcOffset=0)})
        self._plot_widget.setLabel("left", "Temperature (\u00b0C)")
        self._plot_widget.setLabel("bottom", "Date")
        self._plot_widget.setTitle("Hourly Forecast")
        self._plot_widget.addLegend()
        self._disable_plot_menus(self._plot_widget)
        self._precip_view = self._create_precipitation_view(self._plot_widget)
        container_layout.addWidget(self._plot_widget, 1)

    def _create_precipitation_view(self, plot: pg.PlotWidget) -> pg.ViewBox | None:
        plot_item = plot.getPlotItem()
        scene = plot_item.scene()
        if scene is None:
            return None

        plot_item.showAxis("right")
        view = pg.ViewBox()
        view.setMouseEnabled(x=False, y=False)
        scene.addItem(view)

        right_axis = plot_item.getAxis("right")
        right_axis.setLabel("Precipitation (mm)", color="#{:02x}{:02x}{:02x}".format(*PRECIPITATION_COLOR))
        right_axis.linkToView(view)

        view.setXLink(plot_item.vb)
        plot_item.vb.sigResized.connect(self._sync_precipitation_view)
        return view

    def _sync_precipitation_view(self) -> None:
        plot = self._plot_widget
        view = self._precip_view
        if plot is None or view is None or not isValid(plot):
            return
        main_view = plot.getPlotItem().vb
        view.setGeometry(main_view.sceneBoundingRect())
        view.linkedViewChanged(main_view, view.XAxis)

    @staticmethod
    def _disable_plot_menus(plot: pg.PlotWidget) -> None:
        plot_item = plot.getPlotItem()
        plot_item.setMenuEnabled(False, False)
        plot_item.vb.setMenuEnabled(False)
        scene = plot.scene()
        if scene is not None:
            scene.contextMenu = []

    def showEvent(self, event: QShowEvent) -> None:  # ruff: ignore[invalid-function-name]
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

        config = Config()
        client = HttpxClient(config.api_base_url)

        try:
            response = await client.fetch_weather_info(
                latitude=self._place.latitude,
                longitude=self._place.longitude,
                timezone=self._place.timezone,
                forecast_days=self._forecast_days,
                start_day=self._start_day,
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
        precipitation = np.nan_to_num(np.array([r.precipitation for r in hourly], dtype=float), nan=0.0)

        self._plot_widget.clear()
        self._plot_widget.plot(dates, temps, pen="r", name="Temperature")
        self._plot_widget.plot(dates, apparent_temps, pen="b", name="Apparent Temp")
        self._plot_widget.showGrid(x=True, y=True)

        self._update_precipitation(dates, precipitation)
        self._fit_time_range(dates)

    def _update_precipitation(self, dates: np.ndarray, precipitation: np.ndarray) -> None:
        view = self._precip_view
        if view is None:
            return

        for item in list(view.addedItems):
            view.removeItem(item)

        r, g, b = PRECIPITATION_COLOR
        bars = pg.BarGraphItem(
            x=dates,
            height=precipitation,
            width=self._bar_step(dates) * BAR_WIDTH_RATIO,
            brush=pg.mkBrush(r, g, b, PRECIPITATION_BAR_ALPHA),
        )
        view.addItem(bars)
        self._precipitation_bars = bars

        top = max(float(precipitation.max()) * PRECIPITATION_HEADROOM, MIN_PRECIPITATION_AXIS_MAX)
        view.setYRange(0.0, top, padding=0)
        self._sync_precipitation_view()

    def _fit_time_range(self, dates: np.ndarray) -> None:
        if self._plot_widget is None:
            return

        half_step = self._bar_step(dates) / 2

        min_date = float(dates.min())
        max_date = float(dates.max())

        target_min = min_date + (self._start_day * DAY_SECONDS)
        target_max = target_min + (self._forecast_days * DAY_SECONDS)

        x_min = max(min_date - half_step, target_min - half_step)
        x_max = min(max_date + half_step, target_max + half_step)

        plot_item = self._plot_widget.getPlotItem()
        plot_item.setLimits(xMin=x_min, xMax=x_max)
        plot_item.setXRange(x_min, x_max, padding=0)
        plot_item.enableAutoRange(axis="y")

        first = pd.to_datetime(float(dates.min()), unit="s").strftime("%Y-%m-%d")

        last = pd.to_datetime(float(dates.max()), unit="s").strftime("%Y-%m-%d")

        title = f"Hourly Forecast: {first}" if first == last else f"Hourly Forecast: {first} to {last}"
        self._plot_widget.setTitle(title)

    @staticmethod
    def _bar_step(dates: np.ndarray) -> float:
        if dates.size < 2:
            return HOUR_SECONDS
        step = float(np.median(np.abs(np.diff(dates))))
        return step if step > 0 else HOUR_SECONDS

    def _to_epoch(self, value: object) -> float:
        ts = pd.Timestamp(cast("Any", value))
        if ts.tzinfo is not None:
            with contextlib.suppress(Exception):
                ts = ts.tz_convert(self._place.timezone)
            ts = ts.tz_localize(None)
        return float(ts.timestamp())

    def _release_plot(self) -> None:
        plot = self._plot_widget
        if plot is None:
            return
        self._plot_widget = None
        self._precip_view = None
        self._precipitation_bars = None

        with contextlib.suppress(Exception):
            scene = plot.scene()
            export_dialog = getattr(scene, "exportDialog", None)
            if export_dialog is not None and isValid(export_dialog):
                export_dialog.close()
                export_dialog.deleteLater()
            if scene is not None:
                scene.exportDialog = None

        plot.close()
        plot.deleteLater()

    def changeEvent(self, event: QEvent) -> None:  # ruff: ignore[invalid-function-name]
        if event.type() == QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)  # type: ignore[no-untyped-call]
            logger.debug("dialog_language_changed")
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # ruff: ignore[invalid-function-name]
        logger.info("weather_details_dialog_closed", place=self._place.key)
        self._cancel_fetch()
        self._release_plot()
        super().closeEvent(event)
