import pytest
import networkx as nx
from unittest.mock import patch
from app.services.graph_service import find_co2_path, find_fastest_path, compare_paths
from app.services.graph_cache import GraphCache


# ---------------------------------------------------------------------------
# Graphe de test — 4 gares, plusieurs chemins possibles
#
#   Paris ──(CO₂: 2.0, dur: 120)──► Lyon ──(CO₂: 1.5, dur: 60)──► Marseille
#     │                                                                  ▲
#     └────────(CO₂: 5.0, dur: 40)──► Bordeaux ──(CO₂: 0.5, dur: 30)───┘
#
# Chemin CO₂ optimal  : Paris → Lyon → Marseille   (total CO₂ = 3.5)
# Chemin le + rapide  : Paris → Bordeaux → Marseille (total dur = 70 min)
# ---------------------------------------------------------------------------

def make_test_graph() -> nx.DiGraph:
    G = nx.DiGraph()

    G.add_edge("Paris", "Lyon",
        weight_co2=2.0, weight_duration=120,
        trip_id=1, trip_name="TGV 001", agency_name="SNCF",
        co2_kg=2.0, co2_estimated=False,
        distance_km=450, departure_time="08:00", arrival_time="10:00",
    )
    G.add_edge("Lyon", "Marseille",
        weight_co2=1.5, weight_duration=60,
        trip_id=2, trip_name="TGV 002", agency_name="SNCF",
        co2_kg=1.5, co2_estimated=False,
        distance_km=300, departure_time="10:30", arrival_time="11:30",
    )
    G.add_edge("Paris", "Bordeaux",
        weight_co2=5.0, weight_duration=40,
        trip_id=3, trip_name="TGV 003", agency_name="SNCF",
        co2_kg=5.0, co2_estimated=True,  # émission estimée ADEME
        distance_km=580, departure_time="09:00", arrival_time="09:40",
    )
    G.add_edge("Bordeaux", "Marseille",
        weight_co2=0.5, weight_duration=30,
        trip_id=4, trip_name="TGV 004", agency_name="SNCF",
        co2_kg=0.5, co2_estimated=False,
        distance_km=200, departure_time="10:00", arrival_time="10:30",
    )
    return G


# Fixture pytest : patch GraphCache pour ne jamais toucher la DB
@pytest.fixture(autouse=True)
def mock_graph():
    G = make_test_graph()
    GraphCache.set(G)
    yield
    GraphCache.invalidate()


# ---------------------------------------------------------------------------
# Tests find_co2_path
# ---------------------------------------------------------------------------

def test_co2_path_choisit_le_moins_polluant():
    route = find_co2_path("Paris", "Marseille")

    # Doit passer par Lyon, pas Bordeaux
    gares = [s.origin for s in route.steps] + [route.steps[-1].destination]
    assert gares == ["Paris", "Lyon", "Marseille"]

    # CO₂ total = 2.0 + 1.5
    assert route.total_co2_kg == pytest.approx(3.5, rel=1e-4)

    # Une correspondance (2 tronçons)
    assert route.nb_changes == 1

    # Aucune estimation dans ce chemin
    assert route.has_estimated_co2 is False


def test_co2_path_direct():
    # Trajet direct sans correspondance
    route = find_co2_path("Paris", "Lyon")
    assert route.nb_changes == 0
    assert len(route.steps) == 1
    assert route.total_co2_kg == pytest.approx(2.0)


def test_co2_path_gare_inconnue():
    with pytest.raises(ValueError, match="inconnue"):
        find_co2_path("Paris", "Tombouctou")


def test_co2_path_pas_de_chemin():
    # Ajout d'une gare isolée sans arc entrant depuis Paris
    with pytest.raises((ValueError, nx.NetworkXNoPath)):
        find_co2_path("Marseille", "Paris")  # DiGraph, pas d'arc retour


# ---------------------------------------------------------------------------
# Tests find_fastest_path
# ---------------------------------------------------------------------------

def test_fastest_path_choisit_le_plus_rapide():
    route = find_fastest_path("Paris", "Marseille")

    # Doit passer par Bordeaux (40 + 30 = 70 min vs 180 min via Lyon)
    gares = [s.origin for s in route.steps] + [route.steps[-1].destination]
    assert gares == ["Paris", "Bordeaux", "Marseille"]

    assert route.total_duration_minutes == 70

    # Ce chemin contient une émission estimée (Paris→Bordeaux)
    assert route.has_estimated_co2 is True


# ---------------------------------------------------------------------------
# Tests compare_paths
# ---------------------------------------------------------------------------

def test_compare_paths_co2_saved():
    result = compare_paths("Paris", "Marseille")

    # Trajet vert = Paris → Lyon → Marseille
    assert result.co2_optimal.total_co2_kg == pytest.approx(3.5)

    # Trajet rapide = Paris → Bordeaux → Marseille (CO₂ = 5.5)
    assert result.time_optimal.total_co2_kg == pytest.approx(5.5)

    # CO₂ économisé en choisissant le vert
    assert result.co2_saved_kg == pytest.approx(2.0)

    # Le trajet vert prend plus de temps (180 - 70 = 110 min)
    assert result.time_lost_minutes == 110
