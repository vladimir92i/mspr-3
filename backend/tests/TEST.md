"""
Plan de test — API Trajets & Machine Learning
================================================================

Portée (C12) :
Endpoints testés : - GET /trajets (liste des trajets) - GET /trajets/{trip_id} (détail d'un trajet) - GET /ml/predict (prédiction CO2)
Fonction utilitaire testée isolément : - \_is_night(t) (logique métier jour/nuit)

Stratégie : - Tests d'intégration (C10) : appels HTTP réels via FastAPI TestClient
sur l'app complète, connectés à un vrai Postgres (le conteneur
"database" du docker-compose), pas une base simulée. Isolation
assurée par transaction + rollback systématique après chaque test :
aucune donnée de test ne persiste, la base réelle n'est jamais polluée. - Tests unitaires (C9) : logique pure (\_is_night) testée sans passer
par HTTP, pour couvrir les cas limites précisément. - La dépendance `predict_emission` est mockée pour /ml/predict afin de
ne pas dépendre du modèle IA réel (fichiers .joblib) : on teste ici
le contrat de la route (codes HTTP, format de réponse, sécurité),
pas le modèle ML lui-même (qui doit avoir ses propres tests dédiés).

Outils (C12) : - pytest : framework de test - fastapi.testclient : client HTTP synchrone basé sur httpx - sqlmodel + Postgres réel (conteneur "database") : environnement
identique à la prod/dev, pas de simulation qui masquerait des
différences de comportement SQL (contraintes, types, etc.) - unittest.mock.patch : isolation de predict_emission

Couverture visée (C12) : - Cas nominaux (200) pour chaque endpoint - Cas d'erreur attendus par la spec (404, 422, 401) - Cas limites de la fonction \_is_night (bornes incluses, None, jour, nuit) - Vérification du format/contenu de la réponse (pas seulement le code HTTP)

Exécution :
docker compose exec backend pytest tests/test_routes.py -v
"""
