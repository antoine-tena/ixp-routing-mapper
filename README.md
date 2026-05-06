# ISOC631 – IXP Routing Mapper

Projet ISOC631 – Sujet 2 : Étude de la structure de l'Internet mondial via les IXP.

## Objectifs

1. **Recherche d'IXP par localisation** – fonctions de recherche par coordonnées, ville, pays et distance
2. **Carte interactive** – visualisation des IXP colorisés par distance
3. **Analyse des tables de routage PCH** – calcul de la couverture IP par IXP
4. **Graphe des AS** – construction et visualisation du graphe via NetworkX + ForceAtlas2
5. **API REST** – exposition de l'ensemble des fonctionnalités

## Sources de données

- **PeeringDB dump** : export JSON disponible sur le kdrive (voir `data/README.md`)
- **Tables de routage PCH** : <https://www.pch.net/resources/Routing_Data/>

## Installation

```bash
pip install -r requirements.txt
```

## Structure

```
src/
  ixp/
    loader.py      # chargement du dump PeeringDB
    search.py      # 4 fonctions de recherche par localisation
  utils/
    geo.py         # géocodage et distance haversine
tests/
  test_ixp_search.py
data/              # dump PeeringDB (non versionné)
```