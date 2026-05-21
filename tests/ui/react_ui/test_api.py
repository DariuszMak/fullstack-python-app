import pytest
from fastapi.testclient import TestClient

from src.ui.react_ui.app import create_application


@pytest.fixture
def client() -> TestClient:
    app = create_application()
    return TestClient(app)


def test_static_asset_request(client: TestClient) -> None:
    response = client.get("/assets/index-DQ3P1g1z.css")

    assert response.status_code in (200, 404, 304)


def test_favicon_request(client: TestClient) -> None:
    response = client.get("/favicon.ico")

    assert response.status_code == 200


def test_well_known_endpoint(client: TestClient) -> None:
    response = client.get("/.well-known/appspecific/com.chrome.devtools.json")

    assert response.status_code == 204
    assert response.text == ""
