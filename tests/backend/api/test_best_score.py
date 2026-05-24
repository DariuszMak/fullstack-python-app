from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.backend.api.app import app
from src.backend.api.models.best_score_response import BestScoreQueryParams, PlaceBestScoreRecord


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_returns_200(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        response = client.post("/api/v1/weather/best_score", json={})

    assert response.status_code == 200


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_response_has_required_keys(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/best_score", json={}).json()

    assert "results" in data
    assert "threshold" in data
    assert "penalize_rain" in data


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_reflects_threshold(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/best_score", json={"apparent_temperature_threshold": 18.5}).json()

    assert data["threshold"] == pytest.approx(18.5)


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_reflects_penalize_rain(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/best_score", json={"penalize_rain": True}).json()

    assert data["penalize_rain"] is True


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_rejects_forecast_days_out_of_range(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    with TestClient(app) as client:
        r1 = client.post("/api/v1/weather/best_score", json={"forecast_days": 0})
        r2 = client.post("/api/v1/weather/best_score", json={"forecast_days": 17})

    assert r1.status_code == 422
    assert r2.status_code == 422


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_passes_params_to_calculator(mock_calc: MagicMock) -> None:
    mock_calc.return_value = []

    payload = {
        "apparent_temperature_threshold": 22.0,
        "penalize_rain": True,
        "forecast_days": 5,
    }

    with TestClient(app) as client:
        client.post("/api/v1/weather/best_score", json=payload)

    mock_calc.assert_called_once()
    called_params: BestScoreQueryParams = mock_calc.call_args[0][0]
    assert called_params.apparent_temperature_threshold == pytest.approx(22.0)
    assert called_params.penalize_rain is True
    assert called_params.forecast_days == 5


@patch("src.backend.api.routes.calculate_best_scores")
def test_best_score_endpoint_result_fields(mock_calc: MagicMock) -> None:
    mock_calc.return_value = [
        PlaceBestScoreRecord(
            key="jarocin",
            name="Jarocin",
            latitude=51.9727,
            longitude=17.5026,
            timezone="Europe/Berlin",
            score=42.5,
        )
    ]

    with TestClient(app) as client:
        data = client.post("/api/v1/weather/best_score", json={}).json()

    record = data["results"][0]
    assert record["key"] == "jarocin"
    assert record["name"] == "Jarocin"
    assert record["score"] == pytest.approx(42.5)
