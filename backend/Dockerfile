# 1. Utiliser une image officielle Python légère
FROM python:3.11-slim

# 2. Empêcher Python d'écrire des fichiers .pyc sur le disque
ENV PYTHONDONTWRITEBYTECODE 1
# 3. Empêcher Python de mettre en cache la sortie (pour voir les logs en temps réel)
ENV PYTHONUNBUFFERED 1

# 4. Installer les dépendances système nécessaires (ex: pour compiler certaines briques ML/DB)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Définir le répertoire de travail dans le conteneur
WORKDIR /app

# 6. Copier et installer les dépendances Python en premier (optimise le cache Docker)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 7. Copier le reste du code source de l'application
COPY . .

# 8. Exposer le port de l'application FastAPI
EXPOSE 8000

# 9. Lancer l'application avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

CMD ["fastapi", "dev", "main.py", "--host", "0.0.0.0", "--port", "8000"]