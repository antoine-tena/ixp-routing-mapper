"""
Tests unitaires pour le graphe AS (src/routing/graph.py).
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import networkx as nx

from src.routing.graph import build_as_graph, export_graph_json, get_graph_stats

# ── Chemins d'AS synthétiques ─────────────────────────────────────────────────
#  A-B-C, A-B-D  →  arêtes : A-B (×2), B-C (×1), B-D (×1)
FAKE_PATHS = [
    [100, 200, 300],
    [100, 200, 400],
    [500, 600],
]


def _write_table() -> str:
    lines = [
        "*> 1.0.0.0/24   1.1.1.1   0   0   0 100 200 300 i",
        "*> 1.0.1.0/24   1.1.1.1   0   0   0 100 200 400 i",
        "*> 1.0.2.0/24   1.1.1.1   0   0   0 500 600 i",
    ]
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    f.write("\n".join(lines))
    f.close()
    return f.name


class TestBuildAsGraph(unittest.TestCase):

    def setUp(self):
        self.tmpfile = _write_table()

    def tearDown(self):
        os.unlink(self.tmpfile)

    def test_returns_nx_graph(self):
        G = build_as_graph(self.tmpfile)
        self.assertIsInstance(G, nx.Graph)

    def test_nodes_present(self):
        G = build_as_graph(self.tmpfile)
        for asn in [100, 200, 300, 400, 500, 600]:
            self.assertIn(asn, G.nodes())

    def test_edges_present(self):
        G = build_as_graph(self.tmpfile)
        self.assertTrue(G.has_edge(100, 200))
        self.assertTrue(G.has_edge(200, 300))
        self.assertTrue(G.has_edge(200, 400))
        self.assertTrue(G.has_edge(500, 600))

    def test_weight_accumulated(self):
        G = build_as_graph(self.tmpfile)
        # 100-200 apparaît dans les 2 premiers chemins
        self.assertEqual(G[100][200]["weight"], 2)

    def test_weight_single(self):
        G = build_as_graph(self.tmpfile)
        self.assertEqual(G[200][300]["weight"], 1)

    def test_no_self_loops(self):
        G = build_as_graph(self.tmpfile)
        self.assertEqual(list(nx.selfloop_edges(G)), [])

    def test_empty_path_gives_no_edge(self):
        with patch("src.routing.graph.get_as_paths", return_value=[[], [1]]):
            G = build_as_graph(self.tmpfile)
        self.assertEqual(G.number_of_edges(), 0)


class TestExportGraphJson(unittest.TestCase):

    def _make_graph(self):
        G = nx.Graph()
        G.add_edge(100, 200, weight=2)
        G.add_edge(200, 300, weight=1)
        return G

    def test_returns_valid_json(self):
        G = self._make_graph()
        result = export_graph_json(G)
        data = json.loads(result)
        self.assertIn("nodes", data)
        self.assertIn("links", data)

    def test_nodes_count(self):
        G = self._make_graph()
        data = json.loads(export_graph_json(G))
        self.assertEqual(len(data["nodes"]), 3)

    def test_links_count(self):
        G = self._make_graph()
        data = json.loads(export_graph_json(G))
        self.assertEqual(len(data["links"]), 2)

    def test_writes_file(self):
        G = self._make_graph()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "graph.json")
            export_graph_json(G, out)
            self.assertTrue(os.path.exists(out))

    def test_weight_in_links(self):
        G = self._make_graph()
        data = json.loads(export_graph_json(G))
        weights = {(d["source"], d["target"]): d["weight"] for d in data["links"]}
        # Either (100,200) or (200,100) should have weight 2
        found = any(w == 2 for w in weights.values())
        self.assertTrue(found)


class TestGetGraphStats(unittest.TestCase):

    def test_stats_keys(self):
        G = nx.path_graph(4)
        stats = get_graph_stats(G)
        for key in ("nodes", "edges", "density", "avg_degree", "connected_components"):
            self.assertIn(key, stats)

    def test_correct_counts(self):
        G = nx.path_graph(4)  # 4 nodes, 3 edges
        stats = get_graph_stats(G)
        self.assertEqual(stats["nodes"], 4)
        self.assertEqual(stats["edges"], 3)
        self.assertEqual(stats["connected_components"], 1)

    def test_empty_graph(self):
        G = nx.Graph()
        stats = get_graph_stats(G)
        self.assertEqual(stats["nodes"], 0)
        self.assertEqual(stats["avg_degree"], 0)


if __name__ == "__main__":
    unittest.main()
