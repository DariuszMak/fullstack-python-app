import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.routes import router
from src.helpers.config.config import Config

app = FastAPI(
    title="My API",
    version="0.1.0",
    description="API documentation for my service",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


def run_api() -> None:
    config = Config()

    uvicorn_config = uvicorn.Config(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level="info",
    )
    uvicorn.Server(uvicorn_config).run()


if __name__ == "__main__":
    run_api()
