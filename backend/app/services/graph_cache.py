import networkx as nx
from typing import Optional


class GraphCache:
    "Singleton léger qui stocke le graph NetworkX en mémoire. Construit au démarrage via le lifespan FastAPI, puis relu à chaque requête."
    _graph: Optional[nx.DiGraph] = None

    @classmethod
    def set(cls, graph: nx.DiGraph) -> None:
        cls._graph = graph
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        print(f"Graphe mis en cache : {node_count} gares, {edge_count} tronçons")

    @classmethod
    def get(cls) -> nx.DiGraph:
        if cls._graph is None:
            raise RuntimeError(
                "Le graphe n'est pas encore initialisé. Vérifiez que le lifespan FastAPI s'est bien exécuté."
            )
        return cls._graph

    @classmethod
    def invalidate(cls) -> None:
        "Vide le cache au cas où les données DB changent."
        cls._graph = None
        print("Cache graph invalidé.")

    @classmethod
    def is_ready(cls) -> bool:
        return cls._graph is not None