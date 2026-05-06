"""
Tests unitaires pour l'API REST Flask (src/api/app.py).
Utilise le client de test Flask — aucun serveur démarré.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src.api.app import app

FAKE_IXPS = [
    {"id": 1, "name": "AMS-IX", "city": "Amsterdam", "country": "NL",
     "lat": 52.37, "lon": 4.90, "distance_km": 430.0},
    {"id": 2, "name": "LINX", "city": "London", "country": "GB",
     "lat": 51.50, "lon": -0.13, "distance_km": 340.0},
]


class TestIxpByCoordinates(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    @patch("src.api.app.get_ixps_by_coordinates", return_value=FAKE_IXPS)
    def test_ok(self, _mock):
        r = self.client.get("/api/ixp/by-coordinates?lat=48.85&lon=2.35")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(len(data), 2)

    def test_missing_lat(self):
        r = self.client.get("/api/ixp/by-coordinates?lon=2.35")
        self.assertEqual(r.status_code, 400)

    def test_invalid_lat(self):
        r = self.client.get("/api/ixp/by-coordinates?lat=abc&lon=2.35")
        self.assertEqual(r.status_code, 400)


class TestIxpByCity(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    @patch("src.api.app.get_ixps_by_city", return_value=FAKE_IXPS)
    def test_ok(self, _mock):
        r = self.client.get("/api/ixp/by-city?city=Paris&country=FR")
        self.assertEqual(r.status_code, 200)

    def test_missing_city(self):
        r = self.client.get("/api/ixp/by-city?country=FR")
        self.assertEqual(r.status_code, 400)

    @patch("src.api.app.get_ixps_by_city", side_effect=ValueError("not found"))
    def test_unknown_city(self, _mock):
        r = self.client.get("/api/ixp/by-city?city=Nowhere")
        self.assertEqual(r.status_code, 404)


class TestIxpByCountry(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    @patch("src.api.app.get_ixps_by_country", return_value=FAKE_IXPS)
    def test_ok(self, _mock):
        r = self.client.get("/api/ixp/by-country?countries=FR,NL")
        self.assertEqual(r.status_code, 200)

    def test_missing_countries(self):
        r = self.client.get("/api/ixp/by-country")
        self.assertEqual(r.status_code, 400)


class TestIxpWithinDistance(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    @patch("src.api.app.get_ixps_within_distance", return_value=FAKE_IXPS)
    def test_ok(self, _mock):
        r = self.client.get("/api/ixp/within-distance?lat=48.85&lon=2.35&max_km=500")
        self.assertEqual(r.status_code, 200)

    def test_negative_max_km(self):
        r = self.client.get("/api/ixp/within-distance?lat=48.85&lon=2.35&max_km=-1")
        self.assertEqual(r.status_code, 400)

    def test_missing_params(self):
        r = self.client.get("/api/ixp/within-distance?lat=48.85")
        self.assertEqual(r.status_code, 400)


class TestRoutingCoverage(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def _write_table(self):
        lines = ["*> 1.0.0.0/24   1.1.1.1   0   0   0 13335 i"]
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
        f.write("\n".join(lines))
        f.close()
        return f.name

    def test_ok(self):
        tmp = self._write_table()
        try:
            r = self.client.post(
                "/api/routing/coverage",
                json={"filepath": tmp},
            )
            self.assertEqual(r.status_code, 200)
            data = json.loads(r.data)
            self.assertIn("ip_count", data)
        finally:
            os.unlink(tmp)

    def test_missing_filepath(self):
        r = self.client.post("/api/routing/coverage", json={})
        self.assertEqual(r.status_code, 400)

    def test_nonexistent_file(self):
        r = self.client.post("/api/routing/coverage", json={"filepath": "/no/such/file.txt"})
        self.assertEqual(r.status_code, 404)


class TestRoutingGraph(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def _write_table(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
        f.write("*> 1.0.0.0/24   1.1.1.1   0   0   0 100 200 300 i\n")
        f.close()
        return f.name

    def test_graph_ok(self):
        tmp = self._write_table()
        try:
            r = self.client.post("/api/routing/graph", json={"filepath": tmp})
            self.assertEqual(r.status_code, 200)
            data = json.loads(r.data)
            self.assertIn("nodes", data)
            self.assertIn("links", data)
        finally:
            os.unlink(tmp)

    def test_graph_stats_ok(self):
        tmp = self._write_table()
        try:
            r = self.client.post("/api/routing/graph/stats", json={"filepath": tmp})
            self.assertEqual(r.status_code, 200)
            data = json.loads(r.data)
            self.assertIn("nodes", data)
            self.assertIn("edges", data)
        finally:
            os.unlink(tmp)


if __name__ == "__main__":
    unittest.main()
