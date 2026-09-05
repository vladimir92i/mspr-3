from fastapi import APIRouter, HTTPException, Depends

from app.api.deps import verify_api_key
from app.services.ml_service import predict_emission

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
        raise HTTPException(status_code=422, detail=str(e))