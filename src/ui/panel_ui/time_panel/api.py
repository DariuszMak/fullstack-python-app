from typing import Any

import httpx

from src.helpers.config.config import Config


async def fetch_time() -> str:
    config = Config()

    timeout = httpx.Timeout(10.0, connect=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(f"{config.api_base_url}/api/v1/time")
        resp.raise_for_status()
        data: Any = resp.json()
        return str(data["datetime"])
