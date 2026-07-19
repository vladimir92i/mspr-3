import os
import joblib
import pandas as pd
import numpy as np
from collections import deque
from prometheus_client import Histogram, Counter, Gauge
from fastapi import HTTPException

PREDICTION_MEAN = Gauge(
    "ml_co2_prediction_mean",
    "Moyenne glissante des 100 dernières prédictions CO₂"
)

PREDICTION_HISTOGRAM = Histogram(
    "ml_co2_prediction_kg",
    "Distribution des prédictions CO₂ en kg",
    buckets=[0, 1, 2, 5, 10, 20, 50, 100]
)

PREDICTION_COUNT = Counter(
    "ml_prediction_total",
    "Nombre total de prédictions effectuées"
)

IA_MODEL_PATH = "app/services/ia/model_final.joblib"
IA_SCALER_PATH = "app/services/ia/scaler.joblib"

_recent_predictions = deque(maxlen=100)

DISTANCE_MIN_KM = 405
DISTANCE_MAX_KM = 1847

def predict_emission(distance: int) -> float:
    """
    Prédit l'émission CO₂ (kg) d'un trip via le modèle IA du dossier services/IA.
    """
    if distance is None or not (DISTANCE_MIN_KM <= distance <= DISTANCE_MAX_KM):
        raise HTTPException(
            status_code=422,
            detail="La distance doit être comprise entre 405 et 1847"
        )

    try:
        if not os.path.exists(IA_MODEL_PATH) or not os.path.exists(IA_SCALER_PATH):
            raise FileNotFoundError(f"Modèles IA non trouvés aux chemins: {IA_MODEL_PATH}, {IA_SCALER_PATH}")

        model = joblib.load(IA_MODEL_PATH)
        scaler = joblib.load(IA_SCALER_PATH)

        X = pd.DataFrame([[distance]], columns=["distance"])
        X_scaled = scaler.transform(X)
        prediction = model.predict(X_scaled)[0]
        prediction = max(0, prediction)
        prediction = round(float(prediction), 2)

    except FileNotFoundError as e:
        print(f"⚠️  Modèle IA non disponible: {e}")
        print(f"   Utilisation de l'estimation ADEME par défaut")
        prediction = round((distance or 0) * 0.00369, 4)
    except Exception as e:
        print(f"❌ Erreur lors de la prédiction: {e}")
        prediction = round((distance or 0) * 0.00369, 4)

    # --- Mise à jour des métriques Prometheus ---
    PREDICTION_COUNT.inc()
    PREDICTION_HISTOGRAM.observe(prediction)

    _recent_predictions.append(prediction)
    PREDICTION_MEAN.set(sum(_recent_predictions) / len(_recent_predictions))

    return prediction