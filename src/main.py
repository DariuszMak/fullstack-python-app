import os
import sys
import threading
from venv import logger

from src import node_setup, pyside_setup
from src.backend.api.app import run_api
from src.helpers.logging_setup import logging_setup
from src.ui.panel_ui.server import start_panel_in_background
from src.ui.pyside_ui import application
from src.ui.pyside_ui.bootstrap import bootstrap
from src.ui.react_ui.app import start_react_ui_in_background

TRUE_ENV_VARIABLES_VALUES = "true", "1", "t"

logging_setup()

if __name__ == "__main__":
    logger.info("Starting application...")

    if not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")):
        pyside_setup.create_mocs()
        node_setup.build_react_frontend()

    if os.getenv("DOCKER_RUNTIME", "False").lower() not in TRUE_ENV_VARIABLES_VALUES:
        threading.Thread(target=run_api, daemon=True).start()

        start_panel_in_background()
        start_react_ui_in_background()

        _app, loop, _window = bootstrap()

        application.run(loop)
