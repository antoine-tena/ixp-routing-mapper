# Données PeeringDB

Ce dossier contient le dump JSON PeeringDB utilisé comme source de données pour les IXP.

## Téléchargement

Le dump est disponible à l'adresse suivante (accès restreint) :  
https://kdrive.infomaniak.com/app/share/808619/30edf4dd-736c-406d-af58-14d143bac581

Placer le fichier téléchargé ici sous le nom `peeringdb_dump.json`.

## Format attendu

Le loader accepte deux formats :

1. **Format API PeeringDB** – fichier `ix.json` exporté depuis l'API :
   ```json
   { "data": [ { "id": 1, "name": "AMS-IX", "city": "Amsterdam", "country": "NL", ... } ] }
   ```

2. **Format dump complet** – objet racine avec une clé `ix` :
   ```json
   { "ix": { "data": [ ... ] } }
   ```

Les colonnes `lat` / `lon` sont optionnelles : si absentes, le géocodage automatique
sera effectué via Nominatim (OpenStreetMap) à partir du champ `city` + `country`.
