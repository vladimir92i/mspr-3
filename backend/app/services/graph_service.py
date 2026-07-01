import networkx as nx
from app.services.graph_cache import GraphCache
from app.models.graph_models import TripStep, RouteResponse, RouteCompareResponse


def _path_to_route(
    G: nx.DiGraph,
    nodes: list[str],
    origin: str,
    destination: str,
) -> RouteResponse:
    "Convertit une liste de nœuds Dijkstra en RouteResponse."
    steps = []
    for i in range(len(nodes) - 1):
        edge = G[nodes[i]][nodes[i + 1]]
        steps.append(TripStep(
            trip_id=edge["trip_id"],
            trip_name=edge["trip_name"],
            origin=nodes[i],
            destination=nodes[i + 1],
            departure_time=edge.get("departure_time"),
            arrival_time=edge.get("arrival_time"),
            duration_minutes=edge.get("weight_duration"),
            distance_km=edge.get("distance_km"),
            co2_kg=edge["co2_kg"],
            co2_estimated=edge["co2_estimated"],
            agency_name=edge.get("agency_name"),
        ))

    total_co2     = round(sum(s.co2_kg for s in steps), 4)
    total_dur     = sum(s.duration_minutes or 0 for s in steps) or None
    total_dist    = sum(s.distance_km or 0 for s in steps) or None
    has_estimated = any(s.co2_estimated for s in steps)

    return RouteResponse(
        origin=origin,
        destination=destination,
        steps=steps,
        total_co2_kg=total_co2,
        total_duration_minutes=total_dur,
        total_distance_km=total_dist,
        nb_changes=len(steps) - 1,
        has_estimated_co2=has_estimated,
    )

def find_co2_path(origin: str, destination: str) -> RouteResponse:
    G = GraphCache.get()

    if origin not in G:
        raise ValueError(f"Gare de départ inconnue : {origin}")
    if destination not in G:
        raise ValueError(f"Gare d'arrivée inconnue : {destination}")

    nodes = nx.dijkstra_path(G, origin, destination, weight="weight_co2")
    return _path_to_route(G, nodes, origin, destination)

def find_fastest_path(origin: str, destination: str) -> RouteResponse:
    G = GraphCache.get()

    if origin not in G:
        raise ValueError(f"Gare de départ inconnue : {origin}")
    if destination not in G:
        raise ValueError(f"Gare d'arrivée inconnue : {destination}")

    nodes = nx.dijkstra_path(G, origin, destination, weight="weight_duration")
    return _path_to_route(G, nodes, origin, destination)

def compare_paths(origin: str, destination: str) -> RouteCompareResponse:
    G = GraphCache.get()

    for station in (origin, destination):
        if station not in G:
            raise ValueError(f"Gare inconnue : {station}")

    nodes_co2  = nx.dijkstra_path(G, origin, destination, weight="weight_co2")
    nodes_time = nx.dijkstra_path(G, origin, destination, weight="weight_duration")

    route_co2  = _path_to_route(G, nodes_co2,  origin, destination)
    route_time = _path_to_route(G, nodes_time, origin, destination)

    co2_saved = round(route_time.total_co2_kg - route_co2.total_co2_kg, 4)
    time_lost = (
        (route_co2.total_duration_minutes or 0)
        - (route_time.total_duration_minutes or 0)
        if route_co2.total_duration_minutes and route_time.total_duration_minutes
        else None
    )

    return RouteCompareResponse(
        co2_optimal=route_co2,
        time_optimal=route_time,
        co2_saved_kg=co2_saved,
        time_lost_minutes=time_lost,
    )