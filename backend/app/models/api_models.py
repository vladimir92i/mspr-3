from typing import List, Optional, Dict
from datetime import time, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


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
# Référentiel — /gares, /agences, /pays, /sources
# ---------------------------------------------------------------------------

class StationResponse(BaseModel):
    id_station: int
    name: Optional[str]
    city: Optional[str]
    stop_lat: Optional[float]
    stop_lon: Optional[float]
    id_country: int

    class Config:
        from_attributes = True


class CountryResponse(BaseModel):
    id_country: int
    name: Optional[str]
    code_iso: Optional[str]

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id_source: int
    source_dataset: Optional[str]
    format_origin: Optional[str]
    collection_date: Optional[datetime]

    class Config:
        from_attributes = True


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