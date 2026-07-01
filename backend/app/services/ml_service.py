import os
import joblib
import pandas as pd
import numpy as np
from collections import deque
from prometheus_client import Histogram, Counter, Gauge

PREDICTION_MEAN = Gauge(
    "ml_co2_prediction_mean",
    "Moyenne glissante des 100 dernières prédictions CO₂"
)

PREDICTION_HISTOGRAM = Histogram(
    "ml_co2_prediction_kg",
    "Distribution des prédictions CO₂ en kg",
    buckets=[0, 1, 2, 5, 10, 20, 50, 100]  # tranches de CO₂
)

PREDICTION_COUNT = Counter(
    "ml_prediction_total",
    "Nombre total de prédictions effectuées"
)

IA_MODEL_PATH = "app/services/ia/outputs/model_final.joblib"
IA_SCALER_PATH = "app/services/ia/outputs/scaler.joblib"

_recent_predictions = deque(maxlen=100)  # garde les 100 dernières pour le monitoring

DISTANCE_MIN_KM = 405
DISTANCE_MAX_KM = 1847

def predict_emission(distance: int) -> float:
    """
    Prédit l'émission CO₂ (kg) d'un trip via le modèle IA du dossier services/IA.
    """
    if distance is None or not (DISTANCE_MIN_KM <= distance <= DISTANCE_MAX_KM):
        raise ValueError(
            status_code=422,
            detail="La distance doit être comprise entre 405 et 1847"
        )

    # Essayer de charger le modèle et scaler du dossier IA
    try:
        if not os.path.exists(IA_MODEL_PATH) or not os.path.exists(IA_SCALER_PATH):
            raise FileNotFoundError(f"Modèles IA non trouvés aux chemins: {IA_MODEL_PATH}, {IA_SCALER_PATH}")
        
        model = joblib.load(IA_MODEL_PATH)
        scaler = joblib.load(IA_SCALER_PATH)
        
        # Préparation des données (le modèle IA utilise seulement la distance)
        X = pd.DataFrame([[distance]], columns=["distance"])
        
        # Normalisation
        X_scaled = scaler.transform(X)
        
        # Prédiction
        prediction = model.predict(X_scaled)[0]
        
        # Éviter les valeurs négatives
        prediction = max(0, prediction)
        
        return round(float(prediction), 2)
        
    except FileNotFoundError as e:
        # Fallback : si le modèle IA n'existe pas, utiliser l'estimation ADEME
        print(f"⚠️  Modèle IA non disponible: {e}")
        print(f"   Utilisation de l'estimation ADEME par défaut")
        return round((distance or 0) * 0.00369, 4)
    except Exception as e:
        print(f"❌ Erreur lors de la prédiction: {e}")
        # Fallback ADEME en cas d'erreur
        return round((distance or 0) * 0.00369, 4)