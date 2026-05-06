"""
Chargement et mise en cache du dump PeeringDB.

Formats acceptés :
  - {"data": [...]}               (export API /ix)
  - {"ix": {"data": [...]}}       (dump complet multi-entités)
  - [...]                         (liste brute)

Si les colonnes 'lat' / 'lon' sont absentes, elles sont déduites
par géocodage Nominatim depuis les champs 'city' et 'country'.
"""

import json
from pathlib import Path

import pandas as pd

from src.utils.geo import geocode_city

_DEFAULT_DUMP = Path(__file__).parent.parent.parent / "data" / "peeringdb_dump.json"
_df_cache: pd.DataFrame | None = None


def _parse_raw(data: object) -> list[dict]:
    """Extrait la liste d'IXP quel que soit l'enveloppe JSON."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "data" in data:
            return data["data"]
        if "ix" in data:
            return _parse_raw(data["ix"])
    raise ValueError("Format du dump PeeringDB non reconnu.")


def _add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Géocode les IXP sans lat/lon via Nominatim (avec cache)."""
    missing = df["lat"].isna() | df["lon"].isna()
    if not missing.any():
        return df

    print(f"[loader] Géocodage de {missing.sum()} IXP sans coordonnées…")
    for idx in df[missing].index:
        city = df.at[idx, "city"] if "city" in df.columns else ""
        country = df.at[idx, "country"] if "country" in df.columns else ""
        coords = geocode_city(str(city), str(country))
        if coords:
            df.at[idx, "lat"] = coords[0]
            df.at[idx, "lon"] = coords[1]

    return df


def load_ixp_data(filepath: str | Path | None = None, force_reload: bool = False) -> pd.DataFrame:
    """
    Charge les données IXP depuis le dump PeeringDB.

    Parameters
    ----------
    filepath : chemin vers le fichier JSON (défaut : data/peeringdb_dump.json)
    force_reload : ignore le cache mémoire et relit le fichier

    Returns
    -------
    DataFrame avec au minimum : id, name, city, country, lat, lon
    """
    global _df_cache
    if _df_cache is not None and not force_reload:
        return _df_cache

    path = Path(filepath) if filepath else _DEFAULT_DUMP
    if not path.exists():
        raise FileNotFoundError(
            f"Dump PeeringDB introuvable : {path}\n"
            "Téléchargez-le depuis le kdrive et placez-le dans data/peeringdb_dump.json"
        )

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    records = _parse_raw(raw)
    df = pd.DataFrame(records)

    # Normalisation des colonnes lat / lon
    if "long" in df.columns and "lon" not in df.columns:
        df = df.rename(columns={"long": "lon"})
    for col in ("lat", "lon"):
        if col not in df.columns:
            df[col] = None

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    # Géocodage des IXP sans coordonnées
    df = _add_coordinates(df)

    # On ne garde que les IXP effectivement localisés
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    _df_cache = df
    return df
