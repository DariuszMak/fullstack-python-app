import asyncio
import platform

import structlog
from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QGuiApplication, QKeyEvent, QResizeEvent
from PySide6.QtWidgets import QSystemTrayIcon

from src.api.models import ServerTimeResponse
from src.api.client.time_client import TimeClient
from src.app.weather_forecast.gather import gather_data
from src.helpers.config.config import Config
from src.helpers.style_loader import StyleLoader
from src.ui.pyside_ui.clock_widget.view.clock_widget import ClockWidget
from src.ui.pyside_ui.dialog_windows.draggable_window.draggable_main_window import DraggableMainWindow
from src.ui.pyside_ui.dialog_windows.warning_dialog import WarningDialog
from src.ui.pyside_ui.forms.moc_main_window import Ui_MainWindow
from src.ui.pyside_ui.settings import (
    ANIMATION_DURATION,
    MAINWINDOW_HEIGHT,
    MAINWINDOW_RESIZE_RANGE,
    MAINWINDOW_WIDTH,
)
from src.ui.pyside_ui.tray_manager import TrayManager

logger = structlog.get_logger(__name__)


class MainWindow(DraggableMainWindow):
    def __init__(self, fetch_server_time: bool = True) -> None:
        super().__init__()

        self._supports_opacity = QGuiApplication.platformName().lower() not in ["wayland", "xcb"]
        self._is_closing = False
        self._server_time_task: asyncio.Task[None] | None = None

        config = Config()
        self._time_client = TimeClient(config.api_base_url)

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

        self.setMinimumSize(MAINWINDOW_WIDTH - MAINWINDOW_RESIZE_RANGE, MAINWINDOW_HEIGHT - MAINWINDOW_RESIZE_RANGE)
        self.resize(MAINWINDOW_WIDTH, MAINWINDOW_HEIGHT)

        self._ui.pushButton.setText("Click to open dialog window")
        self._ui.pushButton.clicked.connect(self.show_warning_dialog)

        self._ui.btn_minimize.clicked.connect(self.showMinimized)
        self._ui.btn_maximize_restore.clicked.connect(self.toggle_maximize_restore)
        self._ui.btn_close.clicked.connect(self.close)

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
            gather_data()
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
