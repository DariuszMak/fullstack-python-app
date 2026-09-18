import threading

from panel.io.server import serve

from src.helpers.config.config import Config
from src.ui.panel_ui.time_panel.layout import create_layout


def run_panel() -> None:
    config = Config()

    serve(
        {
            "/": create_layout,
        },
        address=config.panel_host,
        port=config.panel_port,
        show=False,
        autoreload=False,
        allow_websocket_origin=[
            f"localhost:{config.panel_port}",
            f"{config.panel_host}:{config.panel_port}",
        ],
    )


def start_panel_in_background() -> None:
    thread = threading.Thread(target=run_panel, daemon=True)
    thread.start()
