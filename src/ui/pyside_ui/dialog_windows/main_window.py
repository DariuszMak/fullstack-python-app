import asyncio
import platform

import structlog
from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QGuiApplication, QKeyEvent, QResizeEvent
from PySide6.QtWidgets import QLabel, QLayout, QSystemTrayIcon

from src.backend.api.models.server_time_response import ServerTimeResponse
from src.backend.api.models.weather_score_response import BestScoreResponse
from src.helpers.config.config import Config
from src.helpers.style_loader import StyleLoader
from src.ui.pyside_ui.clock_widget.view.clock_widget import ClockWidget
from src.ui.pyside_ui.dialog_windows.draggable_window.draggable_main_window import DraggableMainWindow
from src.ui.pyside_ui.dialog_windows.warning_dialog import WarningDialog
from src.ui.pyside_ui.dialog_windows.weather_score_card import WeatherScoreCard
from src.ui.pyside_ui.forms.moc_main_window import Ui_MainWindow
from src.ui.pyside_ui.settings import (
    ANIMATION_DURATION,
    MAINWINDOW_HEIGHT,
    MAINWINDOW_RESIZE_RANGE,
    MAINWINDOW_WIDTH,
)
from src.ui.pyside_ui.tray_manager import TrayManager
from src.ui.shared.client.httpx_client import HttpxClient

logger = structlog.get_logger(__name__)


class MainWindow(DraggableMainWindow):
    def __init__(self, fetch_server_time: bool = True) -> None:
        super().__init__()

        self._supports_opacity = QGuiApplication.platformName().lower() not in ["wayland", "xcb"]
        self._is_closing = False
        self._server_time_task: asyncio.Task[None] | None = None
        self._weather_score_task: asyncio.Task[None] | None = None

        config = Config()
        self._time_client = HttpxClient(config.api_base_url)

        self._tray: TrayManager | None
        if QSystemTrayIcon.isSystemTrayAvailable() and platform.system() != "Linux":
            self._tray = TrayManager(self)
        else:
            self._tray = None
            logger.debug("system_tray_unavailable", platform=platform.system())

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        StyleLoader.style_window(self)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        self._ui.btn_minimize.clicked.connect(self.showMinimized)
        self._ui.btn_maximize_restore.clicked.connect(self.toggle_maximize_restore)
        self._ui.btn_close.clicked.connect(self.close)

        self.setMinimumSize(MAINWINDOW_WIDTH - MAINWINDOW_RESIZE_RANGE, MAINWINDOW_HEIGHT - MAINWINDOW_RESIZE_RANGE)
        self.resize(MAINWINDOW_WIDTH, MAINWINDOW_HEIGHT)

        self._ui.openWindowButton.setText("Click to open dialog window")
        self._ui.openWindowButton.clicked.connect(self.show_warning_dialog)

        self._ui.checkWeatherScoreButton.setText("Get weather score")
        self._ui.checkWeatherScoreButton.clicked.connect(self.check_weather_score)

        self._clock_widget: ClockWidget = ClockWidget()
        layout = self._ui.frame_clock_widget.layout()
        if layout is not None:
            layout.addWidget(self._clock_widget)
        else:
            logger.warning("frame_clock_widget_missing_layout")

        if self._supports_opacity:
            self.fade_in_animation()

        self.installEventFilter(self)

        if fetch_server_time:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.debug("new_event_loop_created")

            loop.call_soon(self.fetch_server_time)

    def fetch_server_time(self) -> None:
        if self._server_time_task and not self._server_time_task.done():
            logger.debug("fetch_task_already_running")
            return

        self._server_time_task = asyncio.create_task(self._fetch_server_time())

    async def _fetch_server_time(self) -> None:
        log = logger.bind(client=type(self._time_client).__name__)
        try:
            log.debug("fetching_server_time")
            result = await self._time_client.fetch_time()
            self._apply_server_time(result)
        except Exception as exc:
            log.exception("server_time_fetch_failed", error=str(exc))

    def _apply_server_time(self, server_time: ServerTimeResponse) -> None:
        logger.info("server_time_applied", timestamp=server_time.datetime.isoformat())
        self._clock_widget.set_current_datetime(server_time.datetime)

    def check_weather_score(self) -> None:
        if self._weather_score_task and not self._weather_score_task.done():
            logger.debug("weather_score_task_already_running")
            return

        self._weather_score_task = asyncio.create_task(self._fetch_weather_score())

    async def _fetch_weather_score(self) -> None:
        log = logger.bind(client=type(self._time_client).__name__)
        try:
            log.debug("fetching_weather_score")
            result = await self._time_client.fetch_weather_score()
            self._apply_weather_score(result)
        except Exception as exc:
            log.exception("weather_score_fetch_failed", error=str(exc))
            self._show_weather_score_error(str(exc))

    def _apply_weather_score(self, result: BestScoreResponse) -> None:
        logger.info("weather_score_applied", result_count=len(result.results))
        self._render_weather_score(result)

    def _render_weather_score(self, result: BestScoreResponse) -> None:
        layout = self._ui.weatherScoreContainerLayout
        self._clear_layout(layout)

        summary = QLabel(
            f"Apparent temperature range: {result.min_threshold:.1f}\u00b0C - {result.max_threshold:.1f}\u00b0C"
            f"   Penalize rain: {result.penalize_rain}   Start day offset: {result.start_day}"
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)

        if not result.results:
            empty_label = QLabel("No matching places found.")
            empty_label.setWordWrap(True)
            layout.addWidget(empty_label)
            layout.addStretch(1)
            return

        sorted_results = sorted(result.results, key=lambda place: place.score, reverse=True)

        max_score = max(place.score for place in sorted_results)
        min_score = min(place.score for place in sorted_results)

        score_range = max_score - min_score

        for place in sorted_results:
            if score_range == 0:
                place.percentage_score = 1.0
            else:
                place.percentage_score = (place.score - min_score) / score_range

        for rank, place in enumerate(sorted_results, start=1):
            layout.addWidget(WeatherScoreCard(place, rank=rank))

        layout.addStretch(1)

    def _show_weather_score_error(self, message: str) -> None:
        layout = self._ui.weatherScoreContainerLayout
        self._clear_layout(layout)

        error_label = QLabel(f"Failed to fetch weather score: {message}")
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: rgb(231, 76, 60);")
        layout.addWidget(error_label)
        layout.addStretch(1)

    @staticmethod
    def _clear_layout(layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def fade_in_animation(self) -> None:
        if not self._supports_opacity:
            return
        logger.debug("starting_fade_in")
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(600)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(0.9)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()

    def fade_out_animation(self) -> None:
        if not self._supports_opacity:
            self._final_close()
            return
        logger.debug("starting_fade_out")
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(ANIMATION_DURATION)
        self.anim.setStartValue(0.9)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.finished.connect(self._final_close)
        self.anim.start()

    def show_warning_dialog(self) -> None:
        dlg = WarningDialog(self)
        dlg._ui.label_title_bar_top.setText("Warning title")
        dlg._ui.label_info.setText("Warning message")

        if dlg.exec_():
            logger.info("dialog_accepted")

        else:
            logger.info("dialog_cancelled")

    def toggle_maximize_restore(self) -> None:
        if self._is_maximized:
            self.showNormal()
        else:
            self.showMaximized()
        self._is_maximized = not self._is_maximized
        logger.debug("window_state_toggled", maximized=self._is_maximized)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        min_width = MAINWINDOW_WIDTH - MAINWINDOW_RESIZE_RANGE
        min_height = MAINWINDOW_HEIGHT - MAINWINDOW_RESIZE_RANGE
        new_width = max(event.size().width(), min_width)
        new_height = max(event.size().height(), min_height)

        if new_width != event.size().width() or new_height != event.size().height():
            self.resize(new_width, new_height)

        super().resizeEvent(event)

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)  # type: ignore[no-untyped-call]

        elif event.type() == QEvent.Type.WindowStateChange and self.isMinimized() and self._tray is not None:
            logger.debug("minimizing_to_tray")
            QTimer.singleShot(0, self._hide_to_tray)

        super().changeEvent(event)

    def _hide_to_tray(self) -> None:
        if self._tray is None:
            return
        self.hide()
        self._tray.notify_hidden()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._supports_opacity and not self._is_closing:
            logger.info("window_close_initiated")
            event.ignore()
            self._clock_widget.reset()
            self.fade_out_animation()
        else:
            logger.debug("window_final_close_event")
            super().closeEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key.Key_R:
                logger.debug("hotkey_refresh_triggered")
                self.fetch_server_time()
                return True

            if event.key() == Qt.Key.Key_Q:
                logger.debug("hotkey_quit_triggered")
                self.close()
                return True

        return super().eventFilter(obj, event)

    def _final_close(self) -> None:
        self._is_closing = True
        logger.info("application_terminated")
        super().close()
