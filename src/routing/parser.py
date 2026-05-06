"""
Parseur de tables de routage BGP (format PCH) – Sujet 2, Tâche 3.

Format d'une ligne PCH :
  *> 1.0.138.0/24  194.42.48.80  0  0  6939 38040 23969 i

On extrait :
  - le préfixe IP (ex. 1.0.138.0/24)
  - le chemin d'AS (ex. [6939, 38040, 23969])

Fonctions publiques :
  parse_routing_table(filepath)       -> list[dict]
  compute_ip_coverage(filepath)       -> dict  (count, total_ips, percentage)
  get_as_paths(filepath)              -> list[list[int]]
"""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Union


# Ligne BGP valide : commence par * ou *>
_BGP_LINE = re.compile(
    r"^\*[>s]?\s+"           # statut (*> ou *  ou *s)
    r"(\d+\.\d+\.\d+\.\d+/\d+)"  # préfixe IPv4 CIDR
    r"\s+\S+"                  # next-hop (ignoré)
    r"(?:\s+\S+){3}"           # metric + local-pref + weight (ignorés)
    r"\s+([\d\s{},]+?)"        # chemin d'AS (entiers, espaces, accolades, virgules)
    r"\s+[ie?]?\s*$"           # origine (i, e, ?)
)

# Les chemins contenant des agrégations ({a,b,c}) sont aplatis
_AS_SET = re.compile(r"\{([^}]+)\}")


def _flatten_as_path(raw: str) -> list[int]:
    """Aplatit un chemin d'AS en liste d'entiers (retire les AS-sets et doublons contigus)."""
    path_str = _AS_SET.sub(lambda m: m.group(1).split(",")[0], raw)
    tokens = path_str.split()
    result: list[int] = []
    for t in tokens:
        try:
            asn = int(t)
            if not result or result[-1] != asn:
                result.append(asn)
        except ValueError:
            pass
    return result


def parse_routing_table(filepath: Union[str, Path]) -> list[dict]:
    """
    Parse un fichier de table de routage PCH.

    Returns
    -------
    Liste de dicts avec les clés :
      - prefix  : str  (ex. "1.0.138.0/24")
      - as_path : list[int]
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    entries: list[dict] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip()
            m = _BGP_LINE.match(line)
            if not m:
                continue
            prefix = m.group(1)
            as_path = _flatten_as_path(m.group(2))
            entries.append({"prefix": prefix, "as_path": as_path})

    return entries


def compute_ip_coverage(filepath: Union[str, Path]) -> dict:
    """
    Calcule la couverture IP accessible depuis un IXP.

    Chaque préfixe est compté une seule fois (les doublons sont dédupliqués).
    La taille d'un préfixe /N est 2^(32-N) adresses.
    Le total IPv4 est 2^32 = 4_294_967_296.

    Returns
    -------
    dict avec :
      - unique_prefixes : int   – nombre de préfixes distincts
      - ip_count        : int   – nombre d'adresses IP couvertes
      - total_ipv4      : int   – 4_294_967_296
      - percentage      : float – pourcentage du total IPv4
    """
    entries = parse_routing_table(filepath)
    seen: set[str] = set()
    total = 0

    for entry in entries:
        pfx = entry["prefix"]
        if pfx in seen:
            continue
        seen.add(pfx)
        try:
            network = ipaddress.IPv4Network(pfx, strict=False)
            total += network.num_addresses
        except ValueError:
            pass

    total_ipv4 = 2 ** 32
    return {
        "unique_prefixes": len(seen),
        "ip_count": total,
        "total_ipv4": total_ipv4,
        "percentage": round(total / total_ipv4 * 100, 8),
    }


def get_as_paths(filepath: Union[str, Path]) -> list[list[int]]:
    """
    Retourne la liste de tous les chemins d'AS du fichier.
    Chaque chemin est une liste d'entiers.
    """
    return [e["as_path"] for e in parse_routing_table(filepath)]
