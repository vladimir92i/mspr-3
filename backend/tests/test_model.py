"""
Tests du MODÈLE d'IA.

Aucun mock : les artefacts .joblib livrés sont réellement chargés et
predict_emission() est réellement appelée. Aucune dépendance à Postgres
ni à Docker.

Exécution depuis le dossier backend/ :
    pytest tests/test_model.py -v

Les chemins d'artefacts de ml_service sont relatifs au répertoire courant,
d'où le chdir vers la racine du backend dans la fixture ci-dessous.
"""

import math
import os

import joblib
import pytest
from fastapi import HTTPException

from app.services.ml_service import (
    IA_MODEL_PATH,
    IA_SCALER_PATH,
    predict_emission,
)

# Facteur d'émission ADEME utilisé par le repli de ml_service.py
ADEME_FACTOR = 0.00369

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def run_from_backend_root(monkeypatch):
    """IA_MODEL_PATH / IA_SCALER_PATH sont relatifs : on se place à la racine."""
    monkeypatch.chdir(BACKEND_ROOT)


def test_artefacts_chargeables():
    """Le modèle et le scaler se désérialisent et attendent 1 feature chacun."""
    model = joblib.load(IA_MODEL_PATH)
    scaler = joblib.load(IA_SCALER_PATH)

    assert model.n_features_in_ == 1
    assert scaler.n_features_in_ == 1
    assert model.n_features_in_ == scaler.n_features_in_


def test_prediction_reelle():
    """predict_emission(800) retourne une valeur finie et positive."""
    prediction = predict_emission(800)

    assert isinstance(prediction, float)
    assert math.isfinite(prediction)
    assert prediction > 0


def test_non_bascule_fallback():
    """La valeur retournée ne provient pas de l'estimation ADEME de repli."""
    prediction = predict_emission(800)
    fallback = 800 * ADEME_FACTOR

    assert abs(prediction - fallback) > 1.0


def test_bornes():
    """Les bornes incluses répondent, hors bornes lève une HTTPException 422."""
    assert predict_emission(405) > 0
    assert predict_emission(1847) > 0

    for distance in (404, 1848):
        with pytest.raises(HTTPException) as exc_info:
            predict_emission(distance)
        assert exc_info.value.status_code == 422
