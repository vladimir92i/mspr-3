from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional

from app.api.deps import verify_api_key
from app.database import get_session
from app.models.database_models import Station, Agency, Country, Source
from app.models.api_models import (
    StationResponse,
    AgencyResponse,
    CountryResponse,
    SourceResponse,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


# ---------------------------------------------------------------------------
# GET /gares
# ---------------------------------------------------------------------------

@router.get(
    "/gares",
    response_model=List[StationResponse],
    tags=["Gares"],
    summary="Liste les gares",
)
def get_all_stations(
    city: Optional[str] = Query(default=None, description="Filtre partiel, insensible à la casse"),
    id_country: Optional[int] = Query(default=None, description="Filtre exact sur le pays"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    statement = select(Station)

    if city:
        statement = statement.where(Station.city.ilike(f"%{city}%"))
    if id_country is not None:
        statement = statement.where(Station.id_country == id_country)

    statement = statement.order_by(Station.id_station).offset(offset).limit(limit)

    return session.exec(statement).all()


# ---------------------------------------------------------------------------
# GET /agences
# ---------------------------------------------------------------------------

@router.get(
    "/agences",
    response_model=List[AgencyResponse],
    tags=["Agences"],
    summary="Liste les opérateurs ferroviaires",
)
def get_all_agencies(
    code: Optional[str] = Query(default=None, description="Filtre exact sur le code opérateur"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    statement = select(Agency)

    if code:
        statement = statement.where(Agency.code == code)

    statement = statement.order_by(Agency.id_agency).offset(offset).limit(limit)

    return session.exec(statement).all()


# ---------------------------------------------------------------------------
# GET /pays
# ---------------------------------------------------------------------------

@router.get(
    "/pays",
    response_model=List[CountryResponse],
    tags=["Pays"],
    summary="Liste les pays",
)
def get_all_countries(
    code_iso: Optional[str] = Query(default=None, description="Filtre exact sur le code ISO"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    statement = select(Country)

    if code_iso:
        statement = statement.where(Country.code_iso == code_iso)

    statement = statement.order_by(Country.id_country).offset(offset).limit(limit)

    return session.exec(statement).all()


# ---------------------------------------------------------------------------
# GET /sources
# ---------------------------------------------------------------------------

@router.get(
    "/sources",
    response_model=List[SourceResponse],
    tags=["Sources"],
    summary="Liste les jeux de données sources",
)
def get_all_sources(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    statement = (
        select(Source)
        .order_by(Source.id_source)
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()
