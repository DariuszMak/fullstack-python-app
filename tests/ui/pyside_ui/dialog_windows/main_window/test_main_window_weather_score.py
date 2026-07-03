from __future__ import annotations

import httpx
import pytest
import respx

from src.ui.shared.client.httpx_client import HttpxClient

BASE_URL = "http://testserver"


def make_response_payload() -> dict[str, object]:
    return {
        "results": [],
        "min_threshold": 20.0,
        "max_threshold": 25.0,
        "penalize_rain": True,
        "start_day": 0,
    }


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather_score_sends_empty_body_when_no_args_given() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/forecast/weather-score").mock(
        return_value=httpx.Response(200, json=make_response_payload())
    )

    client = HttpxClient(BASE_URL)
    await client.fetch_weather_score()

    assert route.called
    request = route.calls.last.request
    assert request.content == b"{}"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather_score_sends_temperature_thresholds() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/forecast/weather-score").mock(
        return_value=httpx.Response(200, json=make_response_payload())
    )

    client = HttpxClient(BASE_URL)
    await client.fetch_weather_score(
        apparent_temperature_min_threshold=10.0,
        apparent_temperature_max_threshold=18.0,
    )

    assert route.called
    request = route.calls.last.request
    httpx.Request("POST", route.calls.last.request.url).content

    import json

    parsed = json.loads(request.content)
    assert parsed == {
        "apparent_temperature_min_threshold": 10.0,
        "apparent_temperature_max_threshold": 18.0,
    }


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather_score_sends_all_optional_parameters() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/forecast/weather-score").mock(
        return_value=httpx.Response(200, json=make_response_payload())
    )

    client = HttpxClient(BASE_URL)
    await client.fetch_weather_score(
        apparent_temperature_min_threshold=5.0,
        apparent_temperature_max_threshold=15.0,
        penalize_rain=False,
        forecast_days=7,
        start_day=1,
    )

    assert route.called

    import json

    parsed = json.loads(route.calls.last.request.content)
    assert parsed == {
        "apparent_temperature_min_threshold": 5.0,
        "apparent_temperature_max_threshold": 15.0,
        "penalize_rain": False,
        "forecast_days": 7,
        "start_day": 1,
    }


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather_score_returns_parsed_response() -> None:
    respx.post(f"{BASE_URL}/api/v1/forecast/weather-score").mock(
        return_value=httpx.Response(200, json=make_response_payload())
    )

    client = HttpxClient(BASE_URL)
    result = await client.fetch_weather_score()

    assert result.min_threshold == 20.0
    assert result.max_threshold == 25.0
    assert result.penalize_rain is True
    assert result.start_day == 0
    assert result.results == []


@pytest.mark.asyncio
@respx.mock
async def test_fetch_weather_score_raises_on_http_error() -> None:
    respx.post(f"{BASE_URL}/api/v1/forecast/weather-score").mock(
        return_value=httpx.Response(500, json={"detail": "server_error"})
    )

    client = HttpxClient(BASE_URL)

    with pytest.raises(httpx.HTTPError):
        await client.fetch_weather_score()
