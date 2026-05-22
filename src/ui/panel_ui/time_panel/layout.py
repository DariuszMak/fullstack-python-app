from __future__ import annotations

from datetime import datetime

import panel as pn
import structlog

from src.ui.panel_ui.time_panel.api import fetch_time
from src.ui.panel_ui.time_panel.clock_widget import ClockWidget

logger = structlog.get_logger(__name__)
pn.extension()


def create_layout() -> pn.Column:
    logger.info("creating_layout")
    clock = ClockWidget(size=300)

    time_display: pn.pane.Markdown = pn.pane.Markdown("No data", sizing_mode="stretch_width")  # type: ignore

    button: pn.widgets.Button = pn.widgets.Button(
        label="Fetch time from API",
        color="primary",
    )  # type: ignore

    async def _fetch() -> None:
        log = logger.bind(action="fetch_server_time")
        try:
            time_display.object = "Loading..."
            log.info("request_started")

            dt_str = await fetch_time()
            dt = datetime.fromisoformat(dt_str)

            clock.set_current_datetime(dt)
            time_display.object = f"Server time: `{dt_str}`"

            log.info("request_successful", server_time=dt_str)
        except Exception as exc:
            log.exception("request_failed", error=str(exc))
            time_display.object = f"Error: `{exc}`"

    def on_click(_: object) -> None:
        logger.debug("button_clicked")
        pn.state.execute(_fetch)

    def _on_load() -> None:
        logger.info("application_payload_loaded")
        pn.state.execute(_fetch)

    button.on_click(on_click)
    pn.state.onload(_on_load)

    return pn.Column(
        "# Server Time",
        clock.panel(),
        button,
        time_display,
        width=400,
    )
