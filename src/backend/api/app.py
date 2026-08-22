import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.routes import router
from src.helpers.config.config import Config

config = Config()

app = FastAPI(
    title="My API",
    version="0.1.0",
    description="API documentation for my service",
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(router)


def run_api() -> None:
    uvicorn_config = uvicorn.Config(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level="info",
    )
    uvicorn.Server(uvicorn_config).run()


if __name__ == "__main__":
    run_api()
