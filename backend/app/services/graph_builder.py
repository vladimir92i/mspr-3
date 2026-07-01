import networkx as nx
from sqlmodel import Session, select
from app.models.database_models import Trip, Agency, Station


def build_graph(session: Session) -> nx.DiGraph:
    """
    Construit un graphe NetworkX représentant le réseau ferroviaire.
    
    - Nœuds : gares (par leur nom)
    - Arêtes : trajets (Trip)
    - Poids : CO₂ (weight_co2) et durée (weight_duration)
    
    Returns:
        Un DiGraph NetworkX avec tous les trajets disponibles
    """
    G = nx.DiGraph()
    
    # Charger tous les trips avec les informations des agencies
    statement = select(Trip, Agency).join(Agency, Trip.id_agency == Agency.id_agency)
    results = session.exec(statement).all()
    
    if not results:
        print("⚠️  Aucun trajet trouvé dans la base de données.")
        return G
    
    for trip, agency in results:
        origin = trip.origin
        destination = trip.destination
        
        # Valider que origin et destination existent
        if not origin or not destination:
            continue
        
        # Ajouter les nœuds s'ils n'existent pas
        if not G.has_node(origin):
            G.add_node(origin)
        if not G.has_node(destination):
            G.add_node(destination)
        
        # Calculer l'émission CO₂ (peut être None)
        co2_kg = float(trip.emission) if trip.emission else 0.0
        co2_estimated = trip.emission is None
        
        # Calculer les poids pour Dijkstra
        weight_co2 = co2_kg if co2_kg > 0 else 1.0  # Évite les poids 0
        weight_duration = trip.duration if trip.duration and trip.duration > 0 else 1.0
        
        # Ajouter l'arête avec tous les métadonnées
        G.add_edge(
            origin,
            destination,
            trip_id=trip.id_trip,
            trip_name=trip.name or f"Trip {trip.id_trip}",
            departure_time=trip.departure_time,
            arrival_time=trip.arrival_time,
            duration_minutes=trip.duration,
            distance_km=trip.distance,
            co2_kg=co2_kg,
            co2_estimated=co2_estimated,
            agency_name=agency.name or "Unknown",
            weight_co2=weight_co2,
            weight_duration=weight_duration,
        )
    
    print(f"✅ Graphe construit : {G.number_of_nodes()} gares, {G.number_of_edges()} tronçons")
    return G
