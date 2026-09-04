from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
HEADERS = {"x-api-key": "obrail-local-api-key"}

def test_predict_valid_distance():
    response = client.get("/api/ml/predict?distance=800", headers=HEADERS)
    assert response.status_code == 200
    assert "predicted_co2_kg" in response.json()

def test_predict_distance_too_low():
    response = client.get("/api/ml/predict?distance=200", headers=HEADERS)
    assert response.status_code == 422

def test_predict_distance_too_high():
    response = client.get("/api/ml/predict?distance=2500", headers=HEADERS)
    assert response.status_code == 422

def test_predict_boundaries():
    for d in (405, 1847):
        response = client.get(f"/api/ml/predict?distance={d}", headers=HEADERS)
        assert response.status_code == 200

def test_predict_missing_api_key():
    response = client.get("/api/ml/predict?distance=800")
    assert response.status_code == 401