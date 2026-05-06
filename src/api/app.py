"""
API REST Flask – Sujet 2, Tâche 5.

Endpoints disponibles :

IXP Search
  GET /api/ixp/by-coordinates?lat=&lon=
  GET /api/ixp/by-city?city=&country=
  GET /api/ixp/by-country?countries=FR,DE
  GET /api/ixp/within-distance?lat=&lon=&max_km=

Map
  GET /api/map?lat=&lon=            → HTML Folium

Routing table (upload ou chemin local)
  POST /api/routing/coverage        body: {"filepath": "..."}
  POST /api/routing/graph           body: {"filepath": "..."}
  POST /api/routing/graph/stats     body: {"filepath": "..."}
"""

from __future__ import annotations

import os
import tempfile

from flask import Flask, jsonify, request, send_file

from src.ixp.map import generate_map
from src.ixp.search import (
    get_ixps_by_city,
    get_ixps_by_coordinates,
    get_ixps_by_country,
    get_ixps_within_distance,
)
from src.routing.graph import build_as_graph, export_graph_json, get_graph_stats
from src.routing.parser import compute_ip_coverage

app = Flask(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _float_param(name: str, required: bool = True):
    val = request.args.get(name)
    if val is None:
        if required:
            raise ValueError(f"Paramètre manquant : '{name}'")
        return None
    try:
        return float(val)
    except ValueError:
        raise ValueError(f"Paramètre '{name}' invalide : attendu un nombre flottant")


def _error(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


# ── IXP endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/ixp/by-coordinates")
def ixp_by_coordinates():
    """GET /api/ixp/by-coordinates?lat=48.85&lon=2.35"""
    try:
        lat = _float_param("lat")
        lon = _float_param("lon")
    except ValueError as e:
        return _error(str(e))
    return jsonify(get_ixps_by_coordinates(lat, lon))


@app.get("/api/ixp/by-city")
def ixp_by_city():
    """GET /api/ixp/by-city?city=Paris&country=FR"""
    city = request.args.get("city", "").strip()
    if not city:
        return _error("Paramètre 'city' requis")
    country = request.args.get("country", "")
    try:
        return jsonify(get_ixps_by_city(city, country))
    except ValueError as e:
        return _error(str(e), 404)


@app.get("/api/ixp/by-country")
def ixp_by_country():
    """GET /api/ixp/by-country?countries=FR,DE&ref_lat=48.85&ref_lon=2.35"""
    raw = request.args.get("countries", "").strip()
    if not raw:
        return _error("Paramètre 'countries' requis (ex. FR ou FR,DE)")
    countries = [c.strip() for c in raw.split(",") if c.strip()]
    try:
        ref_lat = _float_param("ref_lat", required=False)
        ref_lon = _float_param("ref_lon", required=False)
    except ValueError as e:
        return _error(str(e))
    return jsonify(get_ixps_by_country(countries, ref_lat, ref_lon))


@app.get("/api/ixp/within-distance")
def ixp_within_distance():
    """GET /api/ixp/within-distance?lat=48.85&lon=2.35&max_km=500"""
    try:
        lat = _float_param("lat")
        lon = _float_param("lon")
        max_km = _float_param("max_km")
    except ValueError as e:
        return _error(str(e))
    if max_km < 0:
        return _error("'max_km' doit être positif ou nul")
    return jsonify(get_ixps_within_distance(lat, lon, max_km))


# ── Map endpoint ──────────────────────────────────────────────────────────────

@app.get("/api/map")
def ixp_map():
    """GET /api/map?lat=48.85&lon=2.35  → renvoie le fichier HTML Folium"""
    try:
        lat = _float_param("lat")
        lon = _float_param("lon")
    except ValueError as e:
        return _error(str(e))

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    tmp.close()
    try:
        out = generate_map(lat, lon, output_path=tmp.name)
        return send_file(out, mimetype="text/html")
    except ValueError as e:
        return _error(str(e), 404)
    finally:
        # nettoyage différé : le fichier est déjà servi en mémoire par Flask
        pass


# ── Routing table endpoints ───────────────────────────────────────────────────

def _require_filepath() -> tuple[str | None, object | None]:
    """Extrait et valide 'filepath' depuis le corps JSON de la requête."""
    body = request.get_json(silent=True) or {}
    filepath = body.get("filepath", "").strip()
    if not filepath:
        return None, _error("Champ 'filepath' requis dans le corps JSON")
    if not os.path.exists(filepath):
        return None, _error(f"Fichier introuvable : {filepath}", 404)
    return filepath, None


@app.post("/api/routing/coverage")
def routing_coverage():
    """
    POST /api/routing/coverage
    Body JSON : {"filepath": "/chemin/vers/table.txt"}
    """
    filepath, err = _require_filepath()
    if err:
        return err
    try:
        result = compute_ip_coverage(filepath)
        return jsonify(result)
    except Exception as e:
        return _error(str(e), 500)


@app.post("/api/routing/graph")
def routing_graph():
    """
    POST /api/routing/graph
    Body JSON : {"filepath": "..."}
    Retourne le graphe AS au format JSON {nodes, links}.
    """
    filepath, err = _require_filepath()
    if err:
        return err
    try:
        G = build_as_graph(filepath)
        return app.response_class(
            response=export_graph_json(G),
            mimetype="application/json",
        )
    except Exception as e:
        return _error(str(e), 500)


@app.post("/api/routing/graph/stats")
def routing_graph_stats():
    """
    POST /api/routing/graph/stats
    Body JSON : {"filepath": "..."}
    """
    filepath, err = _require_filepath()
    if err:
        return err
    try:
        G = build_as_graph(filepath)
        return jsonify(get_graph_stats(G))
    except Exception as e:
        return _error(str(e), 500)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
