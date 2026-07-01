# 🚀 FastAPI ObRail

Bienvenue dans ton nouveau projet FastAPI. Ce dépôt contient la configuration de base pour démarrer rapidement un environnement de développement local.

## 🛠 Prérequis

Avant de commencer, assure-toi d'avoir installé :
*   **Python 3.9+**
*   **pip** (gestionnaire de paquets Python)
*   Un environnement virtuel (recommandé)

---

## Démarrage Rapide

### 1. Installation des dépendances
Commence par créer un environnement virtuel et installe les modules nécessaires :

```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement (Windows)
.venv\Scripts\activate

# Activer l'environnement (macOS/Linux)
source .venv/bin/activate

# Installer FastAPI et Uvicorn
pip install -r requirements.txt
```

### 2. Lancer le serveur de dev
Utilise la commande suivante pour démarrer l'application avec le **hot-reload**:

```bash
fastapi dev
```
*Le serveur sera accessible sur : **[http://127.0.0.1:8000](http://127.0.0.1:8000)***

---

## Documentation de l'API

*   **Swagger UI (Interactif) :** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — *Idéal pour tester tes routes directement depuis le navigateur.*
*   **ReDoc :** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Structure du Projet

```text
.
├── app/
├── main.py                  # Initialisation FastAPI et inclusion des routers
│   ├── database.py          # Configuration SQLModel (engine, session)
│   ├── models/              # Modèles SQLModel (Tables + Schémas)
│   │   ├── __init__.py
│   │   ├── database_models.py
│   │   └── graph_models.py
│   ├── api/                 # Routes (Endpoints) par domaine
│   │   ├── api.py           # Regroupement des routes
│   │   └── endpoints/
│   │   │   ├── ml.py        # Routes Scikit-Learn
│   │   │   └── graph.py     # Routes NetworkX
│   ├── services/            # Cœur du métier (La "Logique")
│   │   ├── ml_service.py    # Logique Scikit-Learn (predict, train)
│   │   └── graph_service.py # Logique NetworkX (shortest path, centrality)
│   ├── crud/                # Opérations DB pures (Create, Read, Update, Delete)
│   └── services/           # Stockage des modèles .joblib ou .pkl
├── tests/                   # Tes tests unitaires et d'intégration
├── .env                     # Variables d'environnement (DB_URL, etc.)
└── requirements.txt
```