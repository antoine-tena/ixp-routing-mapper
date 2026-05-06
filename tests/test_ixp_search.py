"""
Tests unitaires pour les 4 fonctions de recherche d'IXP (src/ixp/search.py).
Les tests utilisent un mini-dataset synthétique pour ne pas dépendre du dump réel.
"""

import math
import unittest
from unittest.mock import patch

import pandas as pd

from src.utils.geo import haversine


# ── Mini-dataset synthétique ──────────────────────────────────────────────────

FAKE_IXP_DATA = pd.DataFrame(
    [
        {"id": 1, "name": "AMS-IX",   "city": "Amsterdam", "country": "NL", "lat": 52.3676, "lon": 4.9041},
        {"id": 2, "name": "LINX",     "city": "London",    "country": "GB", "lat": 51.5074, "lon": -0.1278},
        {"id": 3, "name": "DE-CIX",   "city": "Frankfurt", "country": "DE", "lat": 50.1109, "lon": 8.6821},
        {"id": 4, "name": "France-IX","city": "Paris",     "country": "FR", "lat": 48.8566, "lon": 2.3522},
        {"id": 5, "name": "SFINX",    "city": "Paris",     "country": "FR", "lat": 48.8400, "lon": 2.3200},
        {"id": 6, "name": "MSK-IX",   "city": "Moscow",    "country": "RU", "lat": 55.7558, "lon": 37.6173},
    ]
)


def _mock_load(filepath=None, force_reload=False):
    return FAKE_IXP_DATA.copy()


# ── Tests haversine ───────────────────────────────────────────────────────────

class TestHaversine(unittest.TestCase):

    def test_same_point_is_zero(self):
        self.assertAlmostEqual(haversine(48.8566, 2.3522, 48.8566, 2.3522), 0.0)

    def test_paris_amsterdam(self):
        # Distance réelle Paris–Amsterdam ≈ 430 km
        d = haversine(48.8566, 2.3522, 52.3676, 4.9041)
        self.assertAlmostEqual(d, 430, delta=10)

    def test_symmetry(self):
        d1 = haversine(48.8566, 2.3522, 51.5074, -0.1278)
        d2 = haversine(51.5074, -0.1278, 48.8566, 2.3522)
        self.assertAlmostEqual(d1, d2, places=6)


# ── Tests fonctions de recherche ─────────────────────────────────────────────

@patch("src.ixp.search.load_ixp_data", side_effect=_mock_load)
class TestGetIxpsByCoordinates(unittest.TestCase):

    def test_returns_all_ixps(self, _mock):
        from src.ixp.search import get_ixps_by_coordinates
        result = get_ixps_by_coordinates(48.8566, 2.3522)
        self.assertEqual(len(result), len(FAKE_IXP_DATA))

    def test_sorted_by_distance(self, _mock):
        from src.ixp.search import get_ixps_by_coordinates
        result = get_ixps_by_coordinates(48.8566, 2.3522)
        distances = [r["distance_km"] for r in result]
        self.assertEqual(distances, sorted(distances))

    def test_nearest_to_paris_is_sfinx_or_france_ix(self, _mock):
        from src.ixp.search import get_ixps_by_coordinates
        result = get_ixps_by_coordinates(48.8566, 2.3522)
        self.assertIn(result[0]["name"], {"France-IX", "SFINX"})

    def test_distance_key_present(self, _mock):
        from src.ixp.search import get_ixps_by_coordinates
        result = get_ixps_by_coordinates(48.8566, 2.3522)
        self.assertIn("distance_km", result[0])


@patch("src.ixp.search.load_ixp_data", side_effect=_mock_load)
@patch("src.ixp.search.geocode_city", return_value=(48.8566, 2.3522))
class TestGetIxpsByCity(unittest.TestCase):

    def test_uses_geocoded_coords(self, _mock_geo, _mock_load):
        from src.ixp.search import get_ixps_by_city
        result = get_ixps_by_city("Paris", "FR")
        self.assertEqual(len(result), len(FAKE_IXP_DATA))
        # Le premier résultat doit être un IXP parisien
        self.assertIn(result[0]["name"], {"France-IX", "SFINX"})

    def test_raises_on_unknown_city(self, _mock_geo, _mock_load):
        from src.ixp.search import get_ixps_by_city
        _mock_geo.return_value = None
        with self.assertRaises(ValueError):
            get_ixps_by_city("CityThatDoesNotExist")


@patch("src.ixp.search.load_ixp_data", side_effect=_mock_load)
class TestGetIxpsByCountry(unittest.TestCase):

    def test_single_country(self, _mock):
        from src.ixp.search import get_ixps_by_country
        result = get_ixps_by_country("FR")
        names = {r["name"] for r in result}
        self.assertEqual(names, {"France-IX", "SFINX"})

    def test_list_of_countries(self, _mock):
        from src.ixp.search import get_ixps_by_country
        result = get_ixps_by_country(["FR", "NL"])
        names = {r["name"] for r in result}
        self.assertEqual(names, {"France-IX", "SFINX", "AMS-IX"})

    def test_unknown_country_returns_empty(self, _mock):
        from src.ixp.search import get_ixps_by_country
        self.assertEqual(get_ixps_by_country("ZZ"), [])

    def test_case_insensitive(self, _mock):
        from src.ixp.search import get_ixps_by_country
        result_upper = get_ixps_by_country("FR")
        result_lower = get_ixps_by_country("fr")
        self.assertEqual(
            {r["id"] for r in result_upper},
            {r["id"] for r in result_lower},
        )

    def test_sorted_by_distance(self, _mock):
        from src.ixp.search import get_ixps_by_country
        result = get_ixps_by_country("FR", ref_lat=48.8566, ref_lon=2.3522)
        distances = [r["distance_km"] for r in result]
        self.assertEqual(distances, sorted(distances))


@patch("src.ixp.search.load_ixp_data", side_effect=_mock_load)
class TestGetIxpsWithinDistance(unittest.TestCase):

    def test_zero_radius_returns_only_exact_match(self, _mock):
        # France-IX est à (48.8566, 2.3522) → distance = 0.0, inclus si rayon = 0
        from src.ixp.search import get_ixps_within_distance
        result = get_ixps_within_distance(48.8566, 2.3522, 0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "France-IX")
        self.assertAlmostEqual(result[0]["distance_km"], 0.0)

    def test_large_radius_returns_all(self, _mock):
        from src.ixp.search import get_ixps_within_distance
        result = get_ixps_within_distance(48.8566, 2.3522, 10_000)
        self.assertEqual(len(result), len(FAKE_IXP_DATA))

    def test_500km_from_paris(self, _mock):
        from src.ixp.search import get_ixps_within_distance
        result = get_ixps_within_distance(48.8566, 2.3522, 500)
        names = {r["name"] for r in result}
        # AMS-IX (~430 km), LINX (~340 km), France-IX, SFINX attendus
        self.assertIn("France-IX", names)
        self.assertIn("LINX", names)
        self.assertIn("AMS-IX", names)
        # Moscow (~2500 km) ne doit pas apparaître
        self.assertNotIn("MSK-IX", names)

    def test_all_within_max_distance(self, _mock):
        from src.ixp.search import get_ixps_within_distance
        max_d = 600
        result = get_ixps_within_distance(48.8566, 2.3522, max_d)
        for r in result:
            self.assertLessEqual(r["distance_km"], max_d)


if __name__ == "__main__":
    unittest.main()
