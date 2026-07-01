from fastapi import APIRouter, HTTPException
from app.services.ml_service import predict_emission

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# ---------------------------------------------------------------------------
# GET /ml/predict
# ---------------------------------------------------------------------------

@router.get("/predict", summary="Prédit l'émission Co2 d'un trip")
def predict(distance: int):
    try:
        return {
            "distance_km": distance,
            "predicted_co2_kg": predict_emission(distance),
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))