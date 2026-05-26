import asyncio
import sys

import structlog
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop  # type: ignore

logger = structlog.get_logger(__name__)


def create_application() -> tuple[QCoreApplication, QEventLoop]:
    logger.info("initializing_application")

    app = QApplication.instance()
    if app is None:
        logger.debug("creating_new_qapplication_instance")
        app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    return app, loop


def run(loop: QEventLoop) -> None:
    try:
        logger.info("application_started", loop_type="QEventLoop")
        with loop:
            sys.exit(loop.run_forever())
    except Exception as e:
        logger.exception("application_failed_to_start", error=str(e))
        sys.exit(1)
