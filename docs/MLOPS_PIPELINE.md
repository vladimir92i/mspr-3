# Chaîne de livraison continue du modèle CO₂ ObRail

Ce document décrit la chaîne MLOps qui valide, entraîne, évalue, teste, empaquette
et publie le modèle de prédiction des émissions de CO₂.

Il couvre l'installation, la configuration, l'exécution locale, le déclenchement
manuel, le débogage de chaque étape et la stratégie de retour arrière.

**Périmètre.** Cette chaîne est distincte de la CI applicative. Elle ne se
déclenche que sur le code de la chaîne (`ml/`) et sur les données (`data/`).

---

## 1. Vue d'ensemble

La chaîne comporte six étapes exécutées en séquence. Chaque étape ne démarre que
si la précédente a réussi ; toute étape en échec interrompt la chaîne et aucune
publication n'a lieu.

| Ordre | Étape | Fichier exécuté | Rôle | Interrompt la chaîne si |
| :---- | :---- | :-------------- | :--- | :---------------------- |
| 1 | Validation des données | `ml/data/validate_data.py` | Vérifie schéma, valeurs nulles, bornes, doublons, volumétrie | Une règle bloquante échoue |
| 2 | Entraînement | `ml/train.py` | Entraîne le modèle et écrit les artefacts | Données ou configuration absentes |
| 3 | Validation du modèle | `ml/evaluate.py` | Mesure R², MAE, RMSE et applique la porte de qualité | Un seuil n'est pas atteint, ou régression |
| 4 | Tests du modèle | `ml/tests/test_model.py` | Vérifie chargement, signature, cohérence, non-régression | Un test échoue |
| 5 | Empaquetage | `.github/workflows/ml-model-cd.yml` | Construit l'image Docker du service de prédiction | La construction échoue |
| 6 | Publication | `.github/workflows/ml-model-cd.yml` | Pousse l'image sur GHCR et publie le rapport | L'authentification ou le push échoue |

### Description de l'enchaînement

Le fichier de données `data/dataset_final.csv` alimente l'étape 1. Si la
validation réussit, l'étape 2 produit cinq artefacts dans `ml/artifacts/`. Ces
artefacts sont transmis aux étapes 3 et 4, qui les évaluent et les testent sans
les modifier. Si les deux réussissent, l'étape 5 construit une image Docker
contenant le modèle validé, et l'étape 6 la publie.

Cette description textuelle est volontairement complète : elle remplace le
schéma d'architecture que l'on trouve habituellement ici. Un diagramme en
caractères ASCII serait restitué caractère par caractère par un lecteur d'écran
et n'apporterait aucune information supplémentaire.

---

## 2. Installation

### 2.1. Prérequis

| Élément | Version | Vérification |
| :------ | :------ | :----------- |
| Python | 3.14 (3.12 minimum) | `python --version` |
| pip | à jour | `python -m pip --version` |
| Git | toute version récente | `git --version` |
| Docker | requis pour les étapes 5 et 6 uniquement | `docker --version` |

### 2.2. Dépendances Python

Les dépendances de la chaîne sont isolées dans `ml/requirements.txt`, distinct de
`backend/requirements.txt`. Les versions y sont épinglées sur celles réellement
utilisées pour produire les artefacts.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r ml/requirements.txt
```

Contenu épinglé : `joblib`, `numpy`, `pandas`, `scikit-learn`, `scipy`,
`xgboost`, `PyYAML`, `pytest`.

### 2.3. Secrets à créer

| Secret | Où le créer | Utilisé par | Obligatoire |
| :----- | :---------- | :---------- | :---------- |
| `GITHUB_TOKEN` | Fourni automatiquement par GitHub Actions | Étape 6 (authentification GHCR) | Oui, aucune action requise |

Aucun secret supplémentaire n'est à créer. La chaîne n'utilise aucune valeur
sensible en dur : le registre, le nom d'image et la version de Python sont des
variables d'environnement définies en tête du workflow.

### 2.4. Autorisation du registre

Pour que la publication réussisse, le dépôt doit autoriser l'écriture de
paquets. Dans **Settings › Actions › General › Workflow permissions**,
sélectionner « Read and write permissions ». Le workflow demande explicitement
`packages: write` sur le seul job qui en a besoin.

---

## 3. Configuration

### 3.1. Seuils versionnés

Tous les seuils sont dans `ml/thresholds.yaml`. Ce fichier est versionné : toute
modification d'un seuil laisse une trace dans l'historique Git.

| Clé | Valeur | Signification |
| :-- | :----- | :------------ |
| `data.min_rows` | 150 | Volumétrie minimale acceptable |
| `data.max_duplicate_ratio` | 0.02 | Part maximale de lignes strictement dupliquées |
| `data.bounds.distance.min_exclusive` | 0 | La distance doit être strictement positive |
| `data.bounds.emission.min` | 0 | L'émission ne peut pas être négative |
| `model.r2_min` | 0.75 | Porte de qualité : R² minimal accepté |
| `model.mae_max` | 2.0 | Erreur absolue moyenne maximale, en kg |
| `model.rmse_max` | 3.0 | Erreur quadratique moyenne maximale, en kg |
| `model.regression_tolerance_r2` | 0.05 | Baisse de R² tolérée face au champion |
| `signature.features` | `['distance']` | Features attendues par le modèle |
| `signature.n_features` | 1 | Nombre de features attendues |

Le seuil `r2_min` est délibérément placé **sous** la performance mesurée
(R² = 0,8474 au 08/09/2026), afin qu'il constitue un plancher et non une
promesse.

### 3.2. Variables d'environnement du workflow

Définies en tête de `.github/workflows/ml-model-cd.yml`.

| Variable | Valeur par défaut | Rôle |
| :------- | :---------------- | :--- |
| `PYTHON_VERSION` | `3.14` | Version de Python installée sur le runner |
| `DATA_PATH` | `data/dataset_final.csv` | Jeu de données d'entraînement |
| `CONFIG_PATH` | `ml/thresholds.yaml` | Fichier de seuils |
| `MODEL_DIR` | `ml/artifacts` | Répertoire de sortie des artefacts |
| `REPORT_DIR` | `ml/reports` | Répertoire des rapports |
| `REGISTRY` | `ghcr.io` | Registre d'images |
| `IMAGE_NAME` | `mspr3-backend` | Nom de l'image publiée |

### 3.3. Chemins des fichiers

| Chemin | Contenu | Versionné |
| :----- | :------ | :-------- |
| `data/dataset_final.csv` | Jeu d'entraînement, 212 lignes, 5 colonnes | Oui |
| `ml/thresholds.yaml` | Seuils de validation | Oui |
| `ml/data/validate_data.py` | Étape 1 | Oui |
| `ml/train.py` | Étape 2 | Oui |
| `ml/evaluate.py` | Étape 3 | Oui |
| `ml/tests/test_model.py` | Étape 4 | Oui |
| `ml/requirements.txt` | Dépendances épinglées | Oui |
| `ml/artifacts/` | Artefacts produits à l'exécution | Non, régénérés |
| `ml/reports/` | Rapports produits à l'exécution | Non, régénérés |
| `ml/champion/evaluation.json` | Modèle de référence pour la non-régression | Optionnel |

Le jeu d'entraînement est versionné dans le dépôt pour rendre la chaîne
reproductible sans dépendre d'une base de données disponible au moment de
l'exécution. Sur un volume supérieur, un outil de versionnement de données tel
que DVC serait le choix adapté.

---

## 4. Déclencheurs

Les quatre déclencheurs sont déclarés explicitement dans le workflow.

| Déclencheur | Condition exacte | Effet | Publication de l'image |
| :---------- | :--------------- | :---- | :--------------------- |
| `push` | Sur `main`, et uniquement si des fichiers de `ml/**`, `data/**` ou du workflow lui-même changent | Chaîne complète, étapes 1 à 6 | Oui |
| `pull_request` | Mêmes filtres de chemins, toute branche cible | Chaîne complète, étapes 1 à 6 | Non : l'image est construite mais pas poussée ; le rapport est commenté sur la pull request |
| `workflow_dispatch` | Déclenchement manuel depuis l'onglet Actions | Chaîne complète, avec paramètres | Oui |
| `schedule` | `cron: "0 3 * * 1"`, soit tous les lundis à 3 h 00 UTC | Réentraînement périodique complet | Oui |

### 4.1. Paramètres du déclenchement manuel

| Paramètre | Valeur par défaut | Effet |
| :-------- | :---------------- | :---- |
| `seed` | `42` | Graine d'entraînement transmise à `ml/train.py` |
| `r2_min` | `0.75` | Surcharge le seuil de `ml/thresholds.yaml` pour cette exécution seulement |

### 4.2. Filtrage par chemins

Le filtre `paths` évite qu'une modification du frontend ne relance
l'entraînement du modèle. Les trois workflows du dépôt sont filtrés de la même
manière :

| Workflow | Chemins surveillés |
| :------- | :----------------- |
| `ml-model-cd.yml` | `ml/**`, `data/**` |
| `backend-ci-cd.yml` | `backend/**` |
| `frontend-ci.yml` | `frontend/**` |

---

## 5. Tester la chaîne

### 5.1. Exécution locale, étape par étape

Chaque étape s'exécute indépendamment et rend un code retour explicite. Après
chaque commande, `echo $?` affiche ce code (`0` signifie succès).

```bash
# Étape 1 : validation des données
python ml/data/validate_data.py \
    --data data/dataset_final.csv \
    --config ml/thresholds.yaml \
    --report ml/reports/data_validation.json

# Étape 2 : entraînement
python ml/train.py \
    --data data/dataset_final.csv \
    --seed 42 \
    --out-dir ml/artifacts

# Étape 3 : validation du modèle
python ml/evaluate.py \
    --model-dir ml/artifacts \
    --config ml/thresholds.yaml \
    --report-dir ml/reports

# Étape 4 : tests du modèle
python -m pytest ml/tests/test_model.py -v
```

### 5.2. Vérifier que la chaîne échoue bien

Une porte de qualité qui ne peut pas échouer ne valide rien. Les deux commandes
suivantes doivent rendre un code retour non nul.

```bash
# La porte de qualité rejette un seuil inatteignable
python ml/evaluate.py --model-dir ml/artifacts --r2-min 0.99
echo $?   # doit afficher 1

# La validation des données rejette un fichier hors bornes
python ml/data/validate_data.py --data /tmp/dataset_corrompu.csv
echo $?   # doit afficher 1
```

### 5.3. Déclenchement manuel sur GitHub

1. Ouvrir l'onglet **Actions** du dépôt.
2. Sélectionner **ML Model CD** dans la liste de gauche.
3. Cliquer sur **Run workflow**.
4. Renseigner `seed` et `r2_min`, ou conserver les valeurs par défaut.
5. Confirmer par **Run workflow**.

Le rapport d'évaluation apparaît dans le résumé de l'exécution, sous
**Summary**, et les artefacts sont téléchargeables en bas de cette même page.

### 5.4. Artefacts produits

| Artefact publié | Contenu | Produit par |
| :-------------- | :------ | :---------- |
| `data-validation-report` | `data_validation.json` | Étape 1 |
| `model-artifacts` | modèle, scaler, features, jeu de test, `metadata.json` | Étape 2 |
| `evaluation-report` | `evaluation.json` et `evaluation.md` | Étape 3 |

---

## 6. Débogage par étape

### 6.1. Étape 1 en échec — validation des données

| Message | Cause probable | Correction |
| :------ | :------------- | :--------- |
| `schema.colonnes_presentes` en FAIL | Une colonne attendue a été renommée ou supprimée | Comparer l'en-tête du CSV avec `data.schema` dans `ml/thresholds.yaml` |
| `schema.type.<colonne>` en FAIL | Type incompatible, souvent une colonne numérique contenant du texte | Inspecter les valeurs non numériques de la colonne concernée |
| `nulls.<colonne>` en FAIL | Valeurs manquantes sur une colonne critique | Corriger la source des données ; ne pas neutraliser la règle |
| `bounds.*` en FAIL | Valeur physiquement impossible (distance nulle ou négative) | Identifier les lignes fautives avant toute modification du seuil |
| `duplicates.lignes_completes` en FAIL | Trop de lignes strictement identiques | Dédoublonner à la source |
| `volume.min_rows` en FAIL | Jeu de données tronqué | Vérifier que le fichier n'a pas été partiellement écrit |

Le rapport `ml/reports/data_validation.json` liste chaque règle, son statut et
son détail chiffré. C'est le premier fichier à ouvrir.

### 6.2. Étape 2 en échec — entraînement

| Message | Cause probable | Correction |
| :------ | :------------- | :--------- |
| `jeu de donnees introuvable` | Chemin erroné ou fichier non versionné | Vérifier `DATA_PATH` et la présence du fichier dans Git |
| `colonnes absentes du jeu de donnees` | Les features de `signature.features` ne sont pas dans le CSV | Aligner `ml/thresholds.yaml` et le jeu de données |
| `commit_sha` à `UNKNOWN` dans `metadata.json` | Exécution hors dépôt Git | Sans gravité en local ; anormal en CI, vérifier l'étape de checkout |

### 6.3. Étape 3 en échec — validation du modèle

C'est l'échec **attendu** quand le modèle se dégrade : la chaîne fait son
travail. Ouvrir `ml/reports/evaluation.md`, qui indique en toutes lettres quel
critère n'est pas respecté.

| Critère en échec | Interprétation | Action |
| :--------------- | :------------- | :----- |
| `r2` | Le modèle explique moins de variance que le plancher accepté | Examiner les données récentes avant de toucher au seuil |
| `mae` ou `rmse` | L'erreur moyenne dépasse la tolérance métier | Idem |
| `non_regression` | Le nouveau modèle est nettement moins bon que le champion | Conserver le champion, ne pas publier |

Ne jamais abaisser un seuil pour faire passer un pipeline. Le seuil décrit ce
qui est acceptable, pas ce qui est obtenu.

### 6.4. Étape 4 en échec — tests du modèle

| Test en échec | Signification |
| :------------ | :------------ |
| `test_le_modele_accepte_exactement_n_features` | La signature du modèle a changé : l'API qui l'appelle cassera |
| `test_scaler_et_modele_partagent_la_meme_signature` | Scaler et modèle sont désynchronisés, artefacts incohérents |
| `test_non_regression_sur_cas_de_reference` | Le comportement numérique a dérivé au-delà de 0,5 kg |
| `test_la_prediction_croit_avec_la_distance_en_tendance` | La relation distance/émission n'est plus cohérente |

### 6.5. Étape 5 en échec — empaquetage

| Symptôme | Cause probable | Correction |
| :------- | :------------- | :--------- |
| `failed to solve` | `backend/Dockerfile` invalide ou contexte erroné | Reproduire en local : `docker build ./backend` |
| Artefact absent | L'étape 2 n'a rien publié | Vérifier le job `train` dans l'exécution |

### 6.6. Étape 6 en échec — publication

| Symptôme | Cause probable | Correction |
| :------- | :------------- | :--------- |
| `denied: permission_denied` | Le dépôt n'autorise pas l'écriture de paquets | Voir la section 2.4 |
| `unauthorized` | Jeton insuffisant | Vérifier que le job déclare `packages: write` |
| Aucun commentaire sur la pull request | Le job manque `pull-requests: write`, ou le rapport est absent | Consulter l'avertissement émis par le job |

---

## 7. Stratégie de retour arrière

La chaîne est conçue pour qu'un retour arrière ne dépende jamais d'une
reconstruction. Trois niveaux, du plus rapide au plus complet.

### 7.1. Niveau 1 — Revenir à l'image précédente

Chaque publication produit trois étiquettes : la version du modèle, le SHA du
commit, et `latest`. Les versions précédentes restent disponibles sur le
registre.

```bash
docker pull ghcr.io/<proprietaire>/mspr3-backend:<version-precedente>
```

Puis redéployer cette étiquette. Aucune reconstruction n'est nécessaire.

### 7.2. Niveau 2 — Restaurer les artefacts du modèle

Le modèle servi par l'API est versionné dans Git, à
`backend/app/services/ia/`. Restaurer la version antérieure :

```bash
git log --oneline -- backend/app/services/ia/
git checkout <commit> -- backend/app/services/ia/
```

### 7.3. Niveau 3 — Revenir sur le code de la chaîne

```bash
git revert <commit-fautif>
```

Le `revert` déclenche à nouveau la chaîne, qui revalide l'état restauré. C'est
la voie à privilégier sur `main` : elle conserve l'historique.

### 7.4. Point de vigilance

L'étape 5 copie le modèle validé dans le contexte de construction **sur le
runner uniquement**. La chaîne ne réécrit jamais `backend/app/services/ia/` dans
le dépôt : la promotion d'un modèle vers l'API reste une décision humaine,
tracée par un commit. C'est ce qui garantit qu'un réentraînement automatique du
lundi matin ne peut pas remplacer silencieusement le modèle servi en production.

---

## 8. Limites connues

Ces limites sont documentées plutôt que passées sous silence.

| Limite | Portée | Conséquence |
| :----- | :----- | :---------- |
| Le modèle n'est pas strictement monotone | 7 baisses locales sur 21 paliers de 50 km ; corrélation de rang 0,8935 | Une distance supérieure peut donner une prédiction inférieure sur certains intervalles |
| Domaine d'entraînement plus étroit que le domaine accepté par l'API | Données de 405 à 1503 km ; l'API accepte jusqu'à 1847 km | Entre 1503 et 1847 km, le modèle extrapole |
| Une seule feature exploitée | `distance` seule, alors que le jeu contient aussi `duration`, `departure_hour`, `id_agency` | Le potentiel du jeu de données n'est pas épuisé |
| Volumétrie faible | 212 lignes | La variance de la validation croisée est élevée |
| Pas de suivi d'expériences | Ni MLflow, ni registre de modèles | Le suivi repose sur `metadata.json` et l'historique Git |

---

## 9. Accessibilité de ce document

Ce document suit les recommandations du **RGAA 4.1**, déclinaison française de
**WCAG 2.1 niveau AA**, appliquées à un document textuel :

- **Hiérarchie de titres sans saut de niveau** : un seul titre de niveau 1, puis
  des niveaux 2 et 3 successifs, ce qui permet la navigation de titre en titre.
- **Tableaux avec en-têtes explicites** : chaque tableau possède une ligne
  d'en-tête décrivant ses colonnes.
- **Aucune information portée par la seule couleur** : les statuts sont écrits
  en toutes lettres (`PASS`, `FAIL`, `WARN`, `ACCEPTE`, `REFUSE`).
- **Aucun schéma en art ASCII** : l'enchaînement des étapes est décrit par un
  tableau et par un paragraphe en langage naturel (section 1), restituables par
  une synthèse vocale. C'est l'équivalent textuel exigé pour tout contenu non
  textuel.
- **Intitulés de liens et de commandes explicites** : chaque bloc de code est
  précédé d'une phrase indiquant ce qu'il fait et ce qu'il doit produire.
- **Langage clair** : phrases courtes, sigles explicités à leur première
  occurrence, unités précisées (kg, km, UTC).

L'accessibilité de l'application web est documentée séparément dans
`frontend/ACCESSIBILITE.md`.

---

## 10. Références internes

| Sujet | Document |
| :---- | :------- |
| Accessibilité du frontend | `frontend/ACCESSIBILITE.md` |
| Plan de test de l'API | `backend/tests/TEST.md` |
| Requêtes SQL du pipeline ETL | `postgresql/SQL.md` |
| Stack Docker Compose | `readme.md` |
