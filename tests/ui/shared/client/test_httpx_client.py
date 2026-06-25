from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.backend.api.models.weather_score_response import BestScoreResponse
from src.ui.shared.client.httpx_client import HttpxClient


def test_fetch_weather_score_returns_parsed_response() -> None:
    payload = {
        "results": [
            {
                "key": "wroclaw",
                "name": "Wroclaw",
                "latitude": 51.1,
                "longitude": 17.0,
                "timezone": "Europe/Warsaw",
                "score": 0.8,
            },
        ],
        "min_threshold": 20.0,
        "max_threshold": 25.0,
        "penalize_rain": True,
        "start_day": 0,
    }

    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def run() -> BestScoreResponse:
        with patch("src.ui.shared.client.httpx_client.httpx.AsyncClient") as mock_client_cls:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_instance

            client = HttpxClient("http://example.com")
            return await client.fetch_weather_score()

    result = asyncio.run(run())

    mock_client.post.assert_called_once_with("http://example.com/api/v1/forecast/weather-score", json={})

    assert isinstance(result, BestScoreResponse)
    assert result.min_threshold == pytest.approx(20.0)
    assert result.max_threshold == pytest.approx(25.0)
    assert result.penalize_rain is True
    assert result.start_day == 0
    assert len(result.results) == 1
    assert result.results[0].name == "Wroclaw"
    assert result.results[0].score == pytest.approx(0.8)


def test_fetch_weather_score_raises_on_http_error() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "error", request=MagicMock(), response=MagicMock()
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def run() -> None:
        with patch("src.ui.shared.client.httpx_client.httpx.AsyncClient") as mock_client_cls:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_instance

            client = HttpxClient("http://example.com")
            await client.fetch_weather_score()

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(run())