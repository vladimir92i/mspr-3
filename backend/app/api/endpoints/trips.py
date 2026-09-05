from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import time

from app.api.deps import verify_api_key
from app.database import get_session
from app.models.database_models import Trip, Agency, Station, Stop
from app.models.api_models import TripResponse, TripDetailResponse, StatsVolumesResponse, StopDetail

router = APIRouter(prefix="/trajets", tags=["Trajets"])

# Nuit = 22h00 → 05h59
NIGHT_START = time(22, 0)
NIGHT_END   = time(5, 59)

def _is_night(t: Optional[time]) -> bool:
    if t is None:
        return False
    return t >= NIGHT_START or t <= NIGHT_END


# ---------------------------------------------------------------------------
# GET /trajets
# ---------------------------------------------------------------------------

@router.get("", response_model=List[TripResponse])
def get_all_trips(session: Session = Depends(get_session)):
    trips = session.exec(
        select(Trip, Agency)
        .join(Agency, Trip.id_agency == Agency.id_agency)
    ).all()
    
    result = []
    for trip, agency in trips:
        trip_dict = trip.model_dump()
        trip_dict["agency_name"] = agency.name
        result.append(trip_dict)
    
    return result

# ---------------------------------------------------------------------------
# GET /trajets/{id}
# ---------------------------------------------------------------------------

@router.get("/{trip_id}", response_model=TripDetailResponse)
def get_trip_detail(trip_id: int, session: Session = Depends(get_session)):
    # Trip + Agency
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trajet {trip_id} introuvable.")

    agency = session.get(Agency, trip.id_agency)

    # Stops + Stations associés
    stops_statement = (
        select(Stop, Station)
        .join(Station, Stop.id_station == Station.id_station)
        .where(Stop.id_trip == trip_id)
        .order_by(Stop.stop_sequence)
    )
    stops_data = session.exec(stops_statement).all()

    stops = [
        {
            "stop_sequence": stop.stop_sequence,
            "station_name": station.name,
            "city": station.city,
            "arrival_time": str(stop.arrival_time) if stop.arrival_time else None,
            "departure_time": str(stop.departure_time) if stop.departure_time else None,
            "latitude": float(station.stop_lat) if station.stop_lat else None,
            "longitude": float(station.stop_lon) if station.stop_lon else None,
        }
        for stop, station in stops_data
    ]

    return {
        "trip": trip,
        "agency": agency,
        "is_night_train": _is_night(trip.departure_time),
        "stops": stops,
    }


# ---------------------------------------------------------------------------
# GET /trajets/stats/volumes
# ---------------------------------------------------------------------------

@router.get("/stats/volumes", response_model=StatsVolumesResponse)
def get_stats_volumes(session: Session = Depends(get_session)):
    trips = session.exec(select(Trip)).all()
    agencies = session.exec(select(Agency)).all()

    nb_total    = len(trips)
    nb_night    = sum(1 for t in trips if _is_night(t.departure_time))
    nb_day      = nb_total - nb_night
    nb_agencies = len(agencies)

    # Nb de trajets par opérateur
    agency_map = {a.id_agency: a.name for a in agencies}
    trips_by_agency: dict[str, int] = {}
    for t in trips:
        name = agency_map.get(t.id_agency, "Inconnu")
        trips_by_agency[name] = trips_by_agency.get(name, 0) + 1

    return {
        "nb_total_trips": nb_total,
        "nb_day_trips": nb_day,
        "nb_night_trips": nb_night,
        "nb_operators": nb_agencies,
        "trips_by_operator": trips_by_agency,
    }


# ---------------------------------------------------------------------------
# GET /trajets/{trip_id}/arrets
# ---------------------------------------------------------------------------

@router.get(
    "/{trip_id}/arrets",
    response_model=List[StopDetail],
    summary="Liste les arrêts d'un trajet",
    dependencies=[Depends(verify_api_key)],
)
def get_trip_stops(
    trip_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trajet {trip_id} introuvable.")

    stops_statement = (
        select(Stop, Station)
        .join(Station, Stop.id_station == Station.id_station)
        .where(Stop.id_trip == trip_id)
        .order_by(Stop.stop_sequence)
        .offset(offset)
        .limit(limit)
    )
    stops_data = session.exec(stops_statement).all()

    return [
        {
            "stop_sequence": stop.stop_sequence,
            "station_name": station.name,
            "city": station.city,
            "arrival_time": str(stop.arrival_time) if stop.arrival_time else None,
            "departure_time": str(stop.departure_time) if stop.departure_time else None,
            "latitude": float(station.stop_lat) if station.stop_lat else None,
            "longitude": float(station.stop_lon) if station.stop_lon else None,
        }
        for stop, station in stops_data
    ]