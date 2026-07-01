# Stack Docker-Compose (Multi-repo)

Ce projet orchestre une architecture complète en microservices. Le code source du Frontend et du Backend est géré dans des **dépôts Git séparés**, clonés indépendamment.

## Architecture Réseau
Pour garantir la sécurité, les réseaux sont segmentés :
*   **`frontend_net`** : Liaison entre Traefik, le Frontend et le Backend.
*   **`backend_net`** : Isolation de la Database (accessible uniquement par le Backend).
*   **`monitor_net`** : Flux dédié au monitoring.

---

## Pré-requis
*   Docker & Docker Compose
*   Git

---

## Installation et Démarrage

### 1. Cloner le projet et ses dépendances
Le Frontend et le Backend sont des **dépôts Git séparés** clonés indépendamment :
```bash
git clone <url-du-depot-principal>
cd ob-rail-bloc-3

# Cloner les sous-projets s'ils ne sont pas déjà présents
git clone git@github.com:MRSP-2026-GRP-A/frontend-Bloc-3.git frontend-Bloc-3
git clone git@github.com:MRSP-2026-GRP-A/backend-bloc-3.git backend-bloc-3

#Ou si c'est pas avec une clé SSH
git clone https://github.com/MRSP-2026-GRP-A/frontend-Bloc-3.git frontend-Bloc-3
git clone https://github.com/MRSP-2026-GRP-A/backend-bloc-3.git backend-bloc-3

```

### 2. Créer le réseau partagé

Pour que database puisse communiquer avec les jobs (située dans un autre projet), il est nécessaire de créer un réseau Docker partagé avant le lancement (si vous l'avez déjà fait en démarrant les jobs alors sautez cette étape).

Dans votre terminal, exécutez la commande suivante :

```bash
docker network create --driver bridge ob-rail_etl_net
```

### 2. Créer les .env
Dans le dossier backend et frontend, à partir de leur .env.example respectif

Pour le frontend : l'url de l'API
Pour le backend : l'url de la DB, User, Password

### 3. Lancer la stack
```bash
docker-compose up -d --build
```
> **Note :** L'option `--build` est importante pour s'assurer que les images sont reconstruites à partir du code actuel de vos submodules.

---

## Travailler avec les Sous-projets
Lorsque vous modifiez le code dans les dossiers `frontend-Bloc-3/` ou `backend-bloc-3/` :

*   **Mettre à jour les sous-projets :** `git pull` dans chaque dossier séparément
*   **Reconstruire un service spécifique :** `docker-compose up -d --build backend`

---

## Notes sur PostgreSQL (v18+)
En cas d'erreur de compatibilité de dossier (`pg_ctlcluster`), réinitialisez le volume :
```bash
docker-compose down -v
docker-compose up -d
```

---

## Accès aux services
*   **Frontend** : /3000
*   **Backend API** : /8000
*   **Monitoring** : /3030

---

## Commandes utiles
| Action | Commande |
| :--- | :--- |
| Voir les logs | `docker-compose logs -f` |
| Arrêter la stack | `docker-compose stop` |
| Tout supprimer (volumes inclus) | `docker-compose down -v` |
```