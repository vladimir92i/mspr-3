from typing import Optional
from decimal import Decimal
from datetime import time, datetime
from sqlmodel import SQLModel, Field

class Agency(SQLModel, table=True):
    __tablename__ = "agency"

    id_agency: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None, max_length=255)
    code: Optional[str] = Field(default=None, max_length=50)

class Country(SQLModel, table=True):
    __tablename__ = "country"

    id_country: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None, max_length=50)
    code_iso: Optional[str] = Field(default=None, max_length=50)

class Station(SQLModel, table=True):
    __tablename__ = "station"

    id_station: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=50)
    stop_lon: Optional[Decimal] = Field(default=None)
    stop_lat: Optional[Decimal] = Field(default=None)
    id_country: int = Field(foreign_key="country.id_country")

class Source(SQLModel, table=True):
    __tablename__ = "source"

    id_source: Optional[int] = Field(default=None, primary_key=True)
    source_dataset: Optional[str] = Field(default=None, max_length=50)
    format_origin: Optional[str] = Field(default=None, max_length=50)
    collection_date: Optional[datetime] = Field(default=None)

class Trip(SQLModel, table=True):
    __tablename__ = "trip"

    id_trip: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None, max_length=50)
    origin: Optional[str] = Field(default=None, max_length=50)
    destination: Optional[str] = Field(default=None, max_length=50)
    departure_time: Optional[time] = Field(default=None)
    arrival_time: Optional[time] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    distance: Optional[int] = Field(default=None)
    emission: Optional[Decimal] = Field(default=None)
    id_agency: int = Field(foreign_key="agency.id_agency")

class Stop(SQLModel, table=True):
    __tablename__ = "stop"

    id_trip: int = Field(foreign_key="trip.id_trip", primary_key=True)
    id_station: int = Field(foreign_key="station.id_station", primary_key=True)
    departure_time: Optional[time] = Field(default=None)
    arrival_time: Optional[time] = Field(default=None)
    stop_sequence: Optional[int] = Field(default=None)