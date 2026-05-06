"""
Génération de la carte Folium des IXP colorisés par distance (Sujet 2 – Tâche 2).

La couleur de chaque marqueur suit un dégradé continu :
  vert (#00cc00) → jaune → orange → rouge (#cc0000)
basé sur la position relative de l'IXP dans la distribution des distances.

Fonction publique :
  generate_map(lat, lon, output_path, filepath) -> str
    Génère un fichier HTML Folium et retourne son chemin.
"""

from __future__ import annotations

import math
from pathlib import Path

import folium

from src.ixp.search import get_ixps_by_coordinates


def _distance_to_color(distance_km: float, min_d: float, max_d: float) -> str:
    """
    Interpolation linéaire vert → rouge sur l'intervalle [min_d, max_d].
    Retourne une couleur CSS hexadécimale.
    """
    if max_d == min_d:
        return "#00cc00"
    t = max(0.0, min(1.0, (distance_km - min_d) / (max_d - min_d)))

    # Vert (0,204,0) → Jaune (255,204,0) → Rouge (204,0,0)
    if t <= 0.5:
        s = t / 0.5
        r = int(0 + s * 255)
        g = 204
        b = 0
    else:
        s = (t - 0.5) / 0.5
        r = int(255 - s * 51)   # 255 → 204
        g = int(204 - s * 204)  # 204 → 0
        b = 0

    return f"#{r:02x}{g:02x}{b:02x}"


def generate_map(
    lat: float,
    lon: float,
    output_path: str | Path = "ixp_map.html",
    filepath: str | None = None,
) -> str:
    """
    Génère une carte Folium des IXP colorisés par distance au point (lat, lon).

    Parameters
    ----------
    lat         : latitude du point de référence
    lon         : longitude du point de référence
    output_path : chemin du fichier HTML à écrire (défaut : ixp_map.html)
    filepath    : chemin vers le dump PeeringDB (optionnel)

    Returns
    -------
    Chemin absolu du fichier HTML généré.
    """
    ixps = get_ixps_by_coordinates(lat, lon, filepath)
    if not ixps:
        raise ValueError("Aucun IXP trouvé dans le dump.")

    distances = [ixp["distance_km"] for ixp in ixps]
    min_d, max_d = min(distances), max(distances)

    m = folium.Map(location=[lat, lon], zoom_start=4, tiles="CartoDB positron")

    # Marqueur du point de référence
    folium.Marker(
        location=[lat, lon],
        popup="Point de référence",
        icon=folium.Icon(color="blue", icon="star"),
    ).add_to(m)

    for ixp in ixps:
        color = _distance_to_color(ixp["distance_km"], min_d, max_d)
        popup_html = (
            f"<b>{ixp.get('name', '?')}</b><br>"
            f"{ixp.get('city', '')}, {ixp.get('country', '')}<br>"
            f"Distance : {ixp['distance_km']:.0f} km"
        )
        folium.CircleMarker(
            location=[ixp["lat"], ixp["lon"]],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{ixp.get('name', '?')} – {ixp['distance_km']:.0f} km",
        ).add_to(m)

    # Légende colorbar (HTML injecté)
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;background:white;
                padding:12px 16px;border-radius:8px;border:1px solid #ccc;
                font-family:Arial,sans-serif;font-size:13px;box-shadow:2px 2px 6px rgba(0,0,0,.2)">
      <b>Distance au point de référence</b><br><br>
      <span style="background:linear-gradient(to right,#00cc00,#ffcc00,#cc0000);
                   display:inline-block;width:160px;height:14px;border-radius:4px"></span><br>
      <div style="display:flex;justify-content:space-between;width:160px;margin-top:2px">
        <span>Proche</span><span>Éloigné</span>
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    out = Path(output_path).resolve()
    m.save(str(out))
    return str(out)
