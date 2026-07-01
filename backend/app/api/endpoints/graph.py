import networkx as nx
from fastapi import APIRouter, HTTPException, Query

from app.services.graph_cache import GraphCache
from app.models.graph_models import RouteResponse, RouteCompareResponse
from app.services.graph_service import (
    find_co2_path,
    find_fastest_path,
    compare_paths,
)

router = APIRouter(prefix="/route", tags=["Itinéraires"])

# ---------------------------------------------------------------------------
# GET /route/co2-optimal
# ---------------------------------------------------------------------------

@router.get("/co2-optimal", response_model=RouteResponse)
def get_co2_optimal_route(
    origin: str = Query(..., description="Nom de la gare de départ", examples=["Paris"]),
    destination: str = Query(..., description="Nom de la gare d'arrivée", examples=["Marseille"]),
):
    try:
        return find_co2_path(origin, destination)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail=f"Aucun itinéraire trouvé entre '{origin}' et '{destination}'.")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

# ---------------------------------------------------------------------------
# GET /route/fastest
# ---------------------------------------------------------------------------

@router.get("/fastest", response_model=RouteResponse)
def get_fastest_route(
    origin: str = Query(..., description="Nom de la gare de départ", examples=["Paris"]),
    destination: str = Query(..., description="Nom de la gare d'arrivée", examples=["Marseille"]),
):
    try:
        return find_fastest_path(origin, destination)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail=f"Aucun itinéraire trouvé entre '{origin}' et '{destination}'.")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

# ---------------------------------------------------------------------------
# GET /route/compare
# ---------------------------------------------------------------------------

@router.get("/compare", response_model=RouteCompareResponse)
def get_compare_routes(
    origin: str = Query(..., description="Nom de la gare de départ", examples=["Paris"]),
    destination: str = Query(..., description="Nom de la gare d'arrivée", examples=["Marseille"]),
):
    try:
        return compare_paths(origin, destination)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail=f"Aucun itinéraire trouvé entre '{origin}' et '{destination}'.")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

# ---------------------------------------------------------------------------
# GET /route/stations
# ---------------------------------------------------------------------------

@router.get(
    "/stations",
    response_model=list[str],
    summary="Liste des gares disponibles",
    description="Retourne toutes les gares présentes dans le graphe, triées alphabétiquement.",
)
def get_stations():
    try:
        G = GraphCache.get()
        return sorted(G.nodes())
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))