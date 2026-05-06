"""
Construction et export du graphe des AS (Sujet 2 – Tâche 4).

Depuis un fichier de table de routage BGP (format PCH), on construit un graphe
non-orienté dont :
  - les nœuds sont des numéros d'AS (int)
  - les arêtes représentent une adjacence dans au moins un chemin d'AS
  - le poids d'une arête = nombre de fois que la paire apparaît dans les chemins

Fonctions publiques :
  build_as_graph(filepath)         -> nx.Graph
  export_graph_json(G, out_path)   -> str   (format JSON compatible D3/vis.js)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import networkx as nx

from src.routing.parser import get_as_paths


def build_as_graph(filepath: Union[str, Path]) -> nx.Graph:
    """
    Construit le graphe des AS à partir d'une table de routage PCH.

    Parameters
    ----------
    filepath : chemin vers le fichier de table de routage

    Returns
    -------
    nx.Graph dont les arêtes ont un attribut 'weight' (nb d'apparitions).
    """
    G = nx.Graph()
    paths = get_as_paths(filepath)

    for path in paths:
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if G.has_edge(u, v):
                G[u][v]["weight"] += 1
            else:
                G.add_edge(u, v, weight=1)

    return G


def export_graph_json(G: nx.Graph, out_path: Union[str, Path, None] = None) -> str:
    """
    Exporte le graphe au format JSON {nodes, links} compatible D3.js / vis.js.

    Parameters
    ----------
    G        : graphe NetworkX
    out_path : chemin du fichier JSON à écrire (optionnel, si None retourne seulement la chaîne)

    Returns
    -------
    Chaîne JSON sérialisée.
    """
    data = {
        "nodes": [{"id": int(n)} for n in G.nodes()],
        "links": [
            {"source": int(u), "target": int(v), "weight": d.get("weight", 1)}
            for u, v, d in G.edges(data=True)
        ],
    }
    json_str = json.dumps(data, indent=2)

    if out_path is not None:
        Path(out_path).write_text(json_str, encoding="utf-8")

    return json_str


def get_graph_stats(G: nx.Graph) -> dict:
    """
    Retourne des statistiques descriptives sur le graphe.

    Returns
    -------
    dict avec : nodes, edges, density, avg_degree, connected_components
    """
    degrees = [d for _, d in G.degree()]
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 6),
        "avg_degree": round(sum(degrees) / len(degrees), 2) if degrees else 0,
        "connected_components": nx.number_connected_components(G),
    }
