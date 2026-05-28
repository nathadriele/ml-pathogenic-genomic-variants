"""
Integration tests for the VariantClassifier API.

Author: VariantClassifier Team
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert "model_loaded" in data
    assert "preprocessor_loaded" in data


def test_predict_endpoint_with_missing_required_fields(client: TestClient) -> None:
    payload = {
        "variant": {
            "chromosome": "chr17",
        }
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_model_info_endpoint(client: TestClient) -> None:
    response = client.get("/model/info")

    assert response.status_code == 200

    data = response.json()

    assert "model_type" in data
    assert "classes" in data
    assert "n_features" in data
