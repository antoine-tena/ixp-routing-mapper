"""
Tests unitaires pour la carte Folium (src/ixp/map.py).
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from src.ixp.map import _distance_to_color


FAKE_IXPS = [
    {"id": 1, "name": "A", "city": "Paris",     "country": "FR", "lat": 48.85, "lon": 2.35, "distance_km": 0.0},
    {"id": 2, "name": "B", "city": "London",    "country": "GB", "lat": 51.50, "lon": -0.12, "distance_km": 340.0},
    {"id": 3, "name": "C", "city": "Moscow",    "country": "RU", "lat": 55.75, "lon": 37.61, "distance_km": 2500.0},
]


class TestDistanceToColor(unittest.TestCase):

    def test_min_distance_is_green(self):
        color = _distance_to_color(0, 0, 100)
        self.assertEqual(color, "#00cc00")

    def test_max_distance_is_red(self):
        color = _distance_to_color(100, 0, 100)
        # rouge : r=204, g=0, b=0
        self.assertEqual(color, "#cc0000")

    def test_midpoint_is_yellow(self):
        color = _distance_to_color(50, 0, 100)
        # t=0.5 → r=255, g=204, b=0
        self.assertEqual(color, "#ffcc00")

    def test_equal_min_max_returns_green(self):
        color = _distance_to_color(42, 42, 42)
        self.assertEqual(color, "#00cc00")

    def test_output_is_valid_hex(self):
        for d in range(0, 101, 10):
            color = _distance_to_color(d, 0, 100)
            self.assertRegex(color, r"^#[0-9a-f]{6}$")


class TestGenerateMap(unittest.TestCase):

    @patch("src.ixp.map.get_ixps_by_coordinates", return_value=FAKE_IXPS)
    def test_generates_html_file(self, _mock):
        from src.ixp.map import generate_map
        with tempfile.TemporaryDirectory() as tmpdir:
            out = generate_map(48.85, 2.35, output_path=os.path.join(tmpdir, "test.html"))
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<html", content.lower())
            self.assertIn("folium", content.lower())

    @patch("src.ixp.map.get_ixps_by_coordinates", return_value=FAKE_IXPS)
    def test_html_contains_ixp_names(self, _mock):
        from src.ixp.map import generate_map
        with tempfile.TemporaryDirectory() as tmpdir:
            out = generate_map(48.85, 2.35, output_path=os.path.join(tmpdir, "test.html"))
            with open(out, encoding="utf-8") as f:
                content = f.read()
            for ixp in FAKE_IXPS:
                self.assertIn(ixp["name"], content)

    @patch("src.ixp.map.get_ixps_by_coordinates", return_value=[])
    def test_empty_ixps_raises(self, _mock):
        from src.ixp.map import generate_map
        with self.assertRaises(ValueError):
            generate_map(48.85, 2.35)


if __name__ == "__main__":
    unittest.main()
