from typing import Any

import structlog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QSplashScreen
from qasync import QEventLoop  # type: ignore

from src.helpers.style_loader import StyleLoader
from src.ui.pyside_ui.application import create_application
from src.ui.pyside_ui.dialog_windows.main_window import MainWindow

logger = structlog.get_logger(__name__)


def bootstrap() -> tuple[Any, QEventLoop, MainWindow]:
    app, loop = create_application()

    pixmap = QPixmap(":/logos/icons/images/program_icon.ico").scaled(
        64,
        64,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    splash = QSplashScreen(pixmap)

    StyleLoader.center_window(splash)

    logger.info("showing splashscreen")

    splash.show()
    app.processEvents()

    window = MainWindow(fetch_server_time=False)

    window.show()

    splash.finish(window)

    logger.info("splashscreen closed")

    QTimer.singleShot(0, window.fetch_server_time)

    return app, loop, window
