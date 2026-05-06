"""
4 fonctions de recherche d'IXP par localisation (Sujet 2 – Tâche 1).

Toutes les fonctions retournent une liste de dicts, chaque dict représentant
un IXP avec au moins les clés :
  id, name, city, country, lat, lon, distance_km
Les résultats sont ordonnés par distance croissante.

Fonctions publiques :
  get_ixps_by_coordinates  – point (lat, lon) de référence
  get_ixps_by_city         – ville (géocodage automatique)
  get_ixps_by_country      – pays ou liste de pays
  get_ixps_within_distance – rayon maximal en km
"""

from __future__ import annotations

from typing import Union

import pandas as pd

from src.ixp.loader import load_ixp_data
from src.utils.geo import geocode_city, haversine

# Colonnes minimales présentes dans chaque résultat
_OUTPUT_COLS = ["id", "name", "city", "country", "lat", "lon", "distance_km"]


def _to_records(df: pd.DataFrame) -> list[dict]:
    """Convertit le DataFrame en liste de dicts avec uniquement les colonnes utiles."""
    available = [c for c in _OUTPUT_COLS if c in df.columns]
    return df[available].to_dict(orient="records")


def _compute_distances(df: pd.DataFrame, ref_lat: float, ref_lon: float) -> pd.DataFrame:
    """Ajoute la colonne distance_km et trie par distance croissante."""
    df = df.copy()
    df["distance_km"] = df.apply(
        lambda row: haversine(ref_lat, ref_lon, row["lat"], row["lon"]),
        axis=1,
    )
    return df.sort_values("distance_km").reset_index(drop=True)


def get_ixps_by_coordinates(
    lat: float,
    lon: float,
    filepath: str | None = None,
) -> list[dict]:
    """
    Retourne tous les IXP triés par distance croissante par rapport au point (lat, lon).

    Parameters
    ----------
    lat : latitude du point de référence (degrés décimaux)
    lon : longitude du point de référence (degrés décimaux)
    filepath : chemin vers le dump PeeringDB (optionnel)

    Returns
    -------
    Liste de dicts IXP ordonnés par distance_km croissante.
    """
    df = load_ixp_data(filepath)
    df = _compute_distances(df, lat, lon)
    return _to_records(df)


def get_ixps_by_city(
    city: str,
    country: str = "",
    filepath: str | None = None,
) -> list[dict]:
    """
    Retourne tous les IXP triés par distance croissante par rapport à une ville.

    Le géocodage est réalisé via Nominatim (OpenStreetMap) avec cache disque.

    Parameters
    ----------
    city    : nom de la ville (ex. "Paris", "Lyon")
    country : code ISO ou nom du pays pour lever les ambiguïtés (ex. "FR")
    filepath : chemin vers le dump PeeringDB (optionnel)

    Returns
    -------
    Liste de dicts IXP ordonnés par distance_km croissante.

    Raises
    ------
    ValueError si la ville ne peut pas être géocodée.
    """
    coords = geocode_city(city, country)
    if coords is None:
        raise ValueError(f"Impossible de géocoder la ville : '{city}, {country}'")
    lat, lon = coords
    return get_ixps_by_coordinates(lat, lon, filepath)


def get_ixps_by_country(
    countries: Union[str, list[str]],
    ref_lat: float | None = None,
    ref_lon: float | None = None,
    filepath: str | None = None,
) -> list[dict]:
    """
    Retourne les IXP situés dans un ou plusieurs pays, triés par distance.

    Si ref_lat / ref_lon ne sont pas fournis, le tri s'effectue par rapport
    au centroïde géographique des IXP du pays.

    Parameters
    ----------
    countries : code ISO 2 (ex. "FR") ou liste de codes (ex. ["FR", "DE"])
    ref_lat   : latitude du point de référence pour le tri (optionnel)
    ref_lon   : longitude du point de référence pour le tri (optionnel)
    filepath  : chemin vers le dump PeeringDB (optionnel)

    Returns
    -------
    Liste de dicts IXP dans les pays demandés, ordonnés par distance_km croissante.
    """
    if isinstance(countries, str):
        countries = [countries]

    # Normalisation en majuscules pour la comparaison
    countries_upper = [c.upper() for c in countries]

    df = load_ixp_data(filepath)
    if "country" not in df.columns:
        raise KeyError("Le dump ne contient pas de colonne 'country'.")

    filtered = df[df["country"].str.upper().isin(countries_upper)].copy()

    if filtered.empty:
        return []

    # Point de référence : centroïde si non fourni
    if ref_lat is None or ref_lon is None:
        ref_lat = filtered["lat"].mean()
        ref_lon = filtered["lon"].mean()

    filtered = _compute_distances(filtered, ref_lat, ref_lon)
    return _to_records(filtered)


def get_ixps_within_distance(
    lat: float,
    lon: float,
    max_distance_km: float,
    filepath: str | None = None,
) -> list[dict]:
    """
    Retourne uniquement les IXP situés à moins de max_distance_km du point (lat, lon).

    Parameters
    ----------
    lat              : latitude du point de référence (degrés décimaux)
    lon              : longitude du point de référence (degrés décimaux)
    max_distance_km  : rayon maximal en kilomètres
    filepath         : chemin vers le dump PeeringDB (optionnel)

    Returns
    -------
    Liste de dicts IXP dans le rayon, ordonnés par distance_km croissante.
    """
    all_ixps = get_ixps_by_coordinates(lat, lon, filepath)
    return [ixp for ixp in all_ixps if ixp["distance_km"] <= max_distance_km]
