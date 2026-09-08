import os
from datetime import time
from typing import Optional
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from main import app
from app.database import get_session
from app.models.database_models import Trip, Agency, Country, Station, Stop
from app.api.endpoints.trips import _is_night, NIGHT_START, NIGHT_END

# ---------------------------------------------------------------------------
# Connexion au Postgres réel (conteneur "database" existant du docker-compose)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://admin:tchou_tchou@database:5432/ObRail",
)

engine = create_engine(TEST_DATABASE_URL)


# ---------------------------------------------------------------------------
# Fixtures — vrai Postgres, isolation via transaction + rollback par test
# ---------------------------------------------------------------------------

@pytest.fixture(name="session")
def session_fixture():
    """
    Ouvre une connexion réelle à Postgres, démarre une transaction, et fait
    tout le travail du test à l'intérieur. join_transaction_mode="create_savepoint"
    fait que les session.commit() internes (dans les fixtures ou les routes)
    utilisent un SAVEPOINT au lieu de clôturer la transaction externe : le
    rollback final reste donc effectif et annule tout, même après un commit().
    """
    SQLModel.metadata.create_all(engine, checkfirst=True)

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_trip(session: Session):
    """Crée une agence + un trajet + une gare + un arrêt cohérents pour les tests."""
    agency = Agency(id_agency=1, name="TrainOp")
    session.add(agency)

    country = Country(id_country=1, name="France", code_iso="FR")
    session.add(country)

    station = Station(
        id_station=1,
        name="Paris",
        city="Paris",
        stop_lat=48.8566,
        stop_lon=2.3522,
        id_country=1,
    )
    session.add(station)

    trip = Trip(
        id_trip=1,
        id_agency=1,
        departure_time=time(14, 0),
    )
    session.add(trip)

    stop = Stop(
        id_trip=1,
        id_station=1,
        stop_sequence=1,
        arrival_time=time(14, 5),
        departure_time=time(14, 10),
    )
    session.add(stop)

    session.commit()
    return trip


# ---------------------------------------------------------------------------
# Tests unitaires : logique métier _is_night (bornes, cas limites)
# ---------------------------------------------------------------------------

class TestIsNight:
    def test_none_is_not_night(self):
        assert _is_night(None) is False

    def test_midday_is_not_night(self):
        assert _is_night(time(14, 0)) is False

    def test_exactly_night_start_is_night(self):
        # Borne incluse : 22:00 doit être considéré comme nuit
        assert _is_night(NIGHT_START) is True

    def test_exactly_night_end_is_night(self):
        # Borne incluse : 05:59 doit être considéré comme nuit
        assert _is_night(NIGHT_END) is True

    def test_just_after_night_end_is_not_night(self):
        assert _is_night(time(6, 0)) is False

    def test_just_before_night_start_is_not_night(self):
        assert _is_night(time(17, 59)) is False

    def test_middle_of_night_is_night(self):
        assert _is_night(time(2, 30)) is True


# ---------------------------------------------------------------------------
# Tests d'intégration : GET /trajets
# ---------------------------------------------------------------------------

class TestGetAllTrips:

    def test_returns_trip_with_agency_name(self, client: TestClient, seeded_trip: Trip):
        response = client.get("/api/trajets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["agency_name"] == "TrainOp"


# ---------------------------------------------------------------------------
#  Tests d'intégration : GET /trajets/{trip_id}
# ---------------------------------------------------------------------------

class TestGetTripDetail:
    def test_unknown_trip_returns_404(self, client: TestClient):
        response = client.get("/api/trajets/9999")
        assert response.status_code == 404
        assert "introuvable" in response.json()["detail"]



# ---------------------------------------------------------------------------
# Tests d'intégration : GET /ml/predict
# ---------------------------------------------------------------------------

class TestPredict:
    VALID_HEADERS = {"x-api-key": "obrail-local-api-key"}

    def test_missing_api_key_returns_401(self, client: TestClient):
        response = client.get("/api/ml/predict", params={"distance": 800})
        assert response.status_code == 401

    def test_wrong_api_key_returns_401(self, client: TestClient):
        response = client.get(
            "/api/ml/predict",
            params={"distance": 800},
            headers={"x-api-key": "mauvaise-cle"},
        )
        assert response.status_code == 401

    @patch("app.api.endpoints.ml.predict_emission")
    def test_valid_distance_returns_prediction(self, mock_predict, client: TestClient):
        mock_predict.return_value = 3.45
        response = client.get(
            "/api/ml/predict",
            params={"distance": 800},
            headers=self.VALID_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["distance_km"] == 800
        assert data["predicted_co2_kg"] == 3.45
        mock_predict.assert_called_once_with(800)

    @patch("app.api.endpoints.ml.predict_emission")
    def test_invalid_distance_returns_422(self, mock_predict, client: TestClient):
        mock_predict.side_effect = ValueError("La distance doit être comprise entre 405 et 1847")
        response = client.get(
            "/api/ml/predict",
            params={"distance": 10},
            headers=self.VALID_HEADERS,
        )
        assert response.status_code == 422
        assert "distance" in response.json()["detail"]

    def test_missing_distance_param_returns_422(self, client: TestClient):
        # FastAPI doit rejeter la requête avant même d'appeler predict_emission
        response = client.get("/api/ml/predict", headers=self.VALID_HEADERS)
        assert response.status_code == 422
