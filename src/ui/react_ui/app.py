import sys
import threading
from collections.abc import Awaitable, Callable
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src import STATIC_CATALOGUE_NAME
from src.helpers.config.config import Config


def create_application(config: Config | None = None) -> FastAPI:
    cfg = config or Config()

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        static_dir = Path(sys._MEIPASS) / STATIC_CATALOGUE_NAME
    else:
        static_dir = Path(__file__).parent / STATIC_CATALOGUE_NAME

    index_html = (static_dir / "index.html").read_text(encoding="utf-8")

    injection = f'<script>window.__APP_CONFIG__ = {{"apiBaseUrl": "{cfg.api_base_url}"}};</script>'
    patched_html = index_html.replace("</head>", f"{injection}\n</head>", 1)

    app = FastAPI()

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    async def root() -> HTMLResponse:
        return HTMLResponse(content=patched_html)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> FileResponse:
        return FileResponse(Path("src/ui/pyside_ui/forms/icons/images/program_icon.ico"))

    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    @app.middleware("http")
    async def ignore_noise_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        if path.startswith("/.well-known") or path.endswith(".map"):
            return Response(status_code=204)
        return await call_next(request)

    return app


app = create_application()


def run_react_ui(host: str | None = None, port: int | None = None, config: Config | None = None) -> None:
    cfg = config or Config()
    host_str: str = str(host or cfg.react_host)
    port_int: int = port or int(cfg.react_port)
    uvicorn.run(create_application(cfg), host=host_str, port=port_int, log_level="info")


def start_react_ui_in_background() -> None:
    config: Config = Config()
    host: str = config.panel_host or "127.0.0.1"
    port: int = config.react_port or 8000

    thread = threading.Thread(
        target=run_react_ui,
        args=(host, port, config),
        daemon=True,
    )
    thread.start()
