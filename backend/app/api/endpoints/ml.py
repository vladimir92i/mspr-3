from fastapi import APIRouter, HTTPException, Depends, Header
import os

from app.services.ml_service import predict_emission

API_KEY = os.environ.get("API_KEY", "obrail-local-api-key")

def verify_api_key(x_api_key: str | None = Header(default=None, alias="x-api-key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Clé API invalide")

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

@router.get("/predict", summary="Prédit l'émission Co2 d'un trip", dependencies=[Depends(verify_api_key)])
def predict(distance: int):
    ...
    try:
        return {
            "distance_km": distance,
            "predicted_co2_kg": predict_emission(distance),
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))y