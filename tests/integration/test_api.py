"""
Testes de integração para API.

Author: VariantClassifier Team
Date: January 2026
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Cliente de teste FastAPI."""
    return TestClient(app)


def test_health_endpoint(client):
    """Testa endpoint de health check."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data
    assert "preprocessor_loaded" in data


def test_predict_endpoint_missing_data(client):
    """Testa predição com dados faltando."""
    response = client.post("/predict", json={
        "variant": {
            "chromosome": "chr17",
            # Faltando campos obrigatórios
        }
    })

    # Deve retornar erro de validação
    assert response.status_code == 422


def test_model_info_endpoint(client):
    """Testa endpoint de informações do modelo."""
    response = client.get("/model/info")

    assert response.status_code == 200

    data = response.json()
    assert "model_type" in data
    assert "classes" in data
    assert "n_features" in data
