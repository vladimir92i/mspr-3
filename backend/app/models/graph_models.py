from typing import List, Optional, Dict
from datetime import time
from decimal import Decimal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Itinéraires (routes existantes)
# ---------------------------------------------------------------------------

class TripStep(BaseModel):
    trip_id: int
    trip_name: Optional[str]
    origin: str
    destination: str
    departure_time: Optional[time]
    arrival_time: Optional[time]
    duration_minutes: Optional[int]
    distance_km: Optional[int]
    co2_kg: float
    co2_estimated: bool
    agency_name: Optional[str] = None


class RouteResponse(BaseModel):
    origin: str
    destination: str
    steps: List[TripStep]
    total_co2_kg: float
    total_duration_minutes: Optional[int]
    total_distance_km: Optional[int]
    nb_changes: int
    has_estimated_co2: bool


class RouteCompareResponse(BaseModel):
    co2_optimal: RouteResponse
    time_optimal: RouteResponse
    co2_saved_kg: float
    time_lost_minutes: Optional[int]


# ---------------------------------------------------------------------------
# Trajets — /trajets
# ---------------------------------------------------------------------------

class TripResponse(BaseModel):
    id_trip: int
    name: Optional[str]
    origin: Optional[str]
    destination: Optional[str]
    departure_time: Optional[time]
    arrival_time: Optional[time]
    duration: Optional[int]
    distance: Optional[int]
    emission: Optional[float]
    agency_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Trajet détail — /trajets/{id}
# ---------------------------------------------------------------------------

class AgencyResponse(BaseModel):
    id_agency: int
    name: Optional[str]
    code: Optional[str]

    class Config:
        from_attributes = True


class StopDetail(BaseModel):
    stop_sequence: Optional[int]
    station_name: Optional[str]
    city: Optional[str]
    arrival_time: Optional[time]
    departure_time: Optional[time]
    latitude: Optional[float]
    longitude: Optional[float]


class TripDetailResponse(BaseModel):
    trip: TripResponse
    agency: Optional[AgencyResponse]
    is_night_train: bool
    stops: List[StopDetail]


# ---------------------------------------------------------------------------
# Stats — /trajets/stats/volumes
# ---------------------------------------------------------------------------

class StatsVolumesResponse(BaseModel):
    nb_total_trips: int
    nb_day_trips: int
    nb_night_trips: int
    nb_operators: int
    trips_by_operator: Dict[str, int]


# ---------------------------------------------------------------------------
# ML — /ml/predict
# ---------------------------------------------------------------------------

class PredictResponse(BaseModel):
    distance_km: int
    duration_min: int
    agency: str
    predicted_co2_kg: float


class TrainResponse(BaseModel):
    status: str
    samples: int
    mae_kg_co2: Optional[float]
    r2_score: Optional[float]