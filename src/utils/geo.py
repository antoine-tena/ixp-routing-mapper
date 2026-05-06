"""
Utilitaires géographiques : haversine et géocodage Nominatim avec cache disque.
"""

import json
import math
import time
from pathlib import Path

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

_CACHE_FILE = Path(__file__).parent.parent.parent / "geocoding_cache.json"
_geocoder: Nominatim | None = None
_geocode_fn = None


def _get_geocoder() -> tuple:
    global _geocoder, _geocode_fn
    if _geocoder is None:
        _geocoder = Nominatim(user_agent="isoc631-ixp-mapper/1.0")
        _geocode_fn = RateLimiter(_geocoder.geocode, min_delay_seconds=1)
    return _geocoder, _geocode_fn


def _load_cache() -> dict:
    if _CACHE_FILE.exists():
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    with open(_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance orthodromique entre deux points (en km)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def geocode_city(city: str, country: str = "") -> tuple[float, float] | None:
    """
    Retourne (lat, lon) pour une ville donnée.
    Utilise un cache disque pour éviter les appels répétés à Nominatim.
    Retourne None si la ville n'est pas trouvée.
    """
    query = f"{city}, {country}".strip(", ")
    cache = _load_cache()

    if query in cache:
        return tuple(cache[query]) if cache[query] else None

    _, geocode_fn = _get_geocoder()
    location = geocode_fn(query, language="en")

    if location is None:
        cache[query] = None
    else:
        cache[query] = [location.latitude, location.longitude]

    _save_cache(cache)
    return (location.latitude, location.longitude) if location else None
