"""Tests du MODELE CO2 ObRail (et non de l'API qui le sert).

Etape 4 de la chaine de livraison continue du modele (C13).

Perimetre : ces tests portent sur l'artefact serialise et sur son
comportement numerique. Ils ne montent pas l'application FastAPI et ne font
aucun appel HTTP ; les tests de l'API vivent dans backend/tests/.

Aucun mock : le modele et le scaler reellement produits par ml/train.py sont
charges depuis le disque et interroges.

Usage :
  python -m pytest ml/tests/test_model.py -v
  MODEL_DIR=ml/artifacts python -m pytest ml/tests/test_model.py -v
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
import yaml
from scipy.stats import spearmanr

MODEL_DIR = Path(os.environ.get("MODEL_DIR", "ml/artifacts"))
CONFIG_PATH = Path(os.environ.get("ML_CONFIG", "ml/thresholds.yaml"))

# Cas de reference : valeurs PRODUITES par le modele livre puis figees ici.
# Elles n'ont pas ete choisies, elles ont ete mesurees (voir la section
# "Verification" de docs/MLOPS_PIPELINE.md). Toute derive au-dela de la
# tolerance signale un changement de comportement du modele.
REFERENCE_CASES = [
    (500, 10.3011),
    (700, 9.7028),
    (1000, 16.9929),
    (1300, 16.9128),
    (1500, 25.4031),
]
REFERENCE_TOLERANCE_KG = 0.5

# Le modele est un ensemble d'arbres sur une seule variable : il est croissant
# en tendance mais PAS strictement monotone (mesure : 7 baisses locales sur 21
# paliers de 50 km, correlation de Spearman 0.8935). On teste donc la tendance
# par correlation de rang, ce que le modele fait reellement, plutot qu'une
# croissance stricte qui echouerait.
SPEARMAN_MIN = 0.85


@pytest.fixture(scope="module")
def config() -> dict:
    assert CONFIG_PATH.exists(), f"Configuration introuvable : {CONFIG_PATH}"
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def model():
    path = MODEL_DIR / "model_final.joblib"
    assert path.exists(), f"Modele introuvable : {path}. Lancer ml/train.py d'abord."
    return joblib.load(path)


@pytest.fixture(scope="module")
def scaler():
    path = MODEL_DIR / "scaler.joblib"
    assert path.exists(), f"Scaler introuvable : {path}. Lancer ml/train.py d'abord."
    return joblib.load(path)


@pytest.fixture(scope="module")
def metadata() -> dict:
    path = MODEL_DIR / "metadata.json"
    assert path.exists(), f"metadata.json introuvable : {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _predict(model, scaler, distances: list[int]) -> np.ndarray:
    X = pd.DataFrame({"distance": distances})
    return model.predict(scaler.transform(X))


# ---------------------------------------------------------------------------
# 1. Chargement
# ---------------------------------------------------------------------------


def test_le_modele_se_charge(model):
    assert model is not None
    assert hasattr(model, "predict"), "L'objet charge n'expose pas predict()"


def test_le_modele_est_lestimateur_attendu(model, metadata):
    assert type(model).__name__ == metadata["estimator"]["class"], (
        f"Estimateur charge : {type(model).__name__}, "
        f"attendu d'apres metadata : {metadata['estimator']['class']}"
    )
    assert type(model).__name__ == "XGBRegressor"


def test_le_scaler_se_charge(scaler):
    assert hasattr(scaler, "transform"), "L'objet charge n'expose pas transform()"
    assert type(scaler).__name__ == "StandardScaler"


# ---------------------------------------------------------------------------
# 2. Signature : nombre de features
# ---------------------------------------------------------------------------


def test_le_modele_accepte_exactement_n_features(model, config):
    n_expected = config["signature"]["n_features"]
    assert model.n_features_in_ == n_expected, (
        f"Le modele declare n_features_in_={model.n_features_in_}, attendu {n_expected}"
    )


def test_prediction_avec_le_bon_nombre_de_features(model, scaler, config):
    n = config["signature"]["n_features"]
    X = np.array([[800.0]])
    assert X.shape[1] == n
    y = model.predict(scaler.transform(pd.DataFrame(X, columns=["distance"])))
    assert y.shape == (1,)
    assert np.isfinite(y[0]), "La prediction n'est pas un nombre fini"


@pytest.mark.parametrize("n_features", [2, 3, 5])
def test_le_modele_rejette_un_nombre_de_features_incorrect(model, n_features):
    """Un vecteur de mauvaise dimension doit lever, pas produire un resultat."""
    X_wrong = np.ones((1, n_features))
    with pytest.raises(Exception):
        model.predict(X_wrong)


@pytest.mark.parametrize("n_features", [2, 3])
def test_le_scaler_rejette_un_nombre_de_features_incorrect(scaler, n_features):
    X_wrong = np.ones((1, n_features))
    with pytest.raises(Exception):
        scaler.transform(X_wrong)


# ---------------------------------------------------------------------------
# 3. Coherence scaler / modele
# ---------------------------------------------------------------------------


def test_scaler_et_modele_partagent_la_meme_signature(model, scaler):
    assert scaler.n_features_in_ == model.n_features_in_, (
        f"Le scaler attend {scaler.n_features_in_} feature(s) mais le modele "
        f"en attend {model.n_features_in_} : la chaine est incoherente."
    )


def test_le_scaler_porte_les_noms_de_features_attendus(scaler, config):
    expected = list(config["signature"]["features"])
    actual = list(getattr(scaler, "feature_names_in_", []))
    assert actual == expected, f"feature_names_in_ = {actual}, attendu {expected}"


def test_la_sortie_du_scaler_alimente_directement_le_modele(model, scaler):
    """Verifie le chainage reel : transform() puis predict() sans adaptation."""
    X = pd.DataFrame({"distance": [405, 900, 1503]})
    X_scaled = scaler.transform(X)
    assert X_scaled.shape[1] == model.n_features_in_
    y = model.predict(X_scaled)
    assert y.shape == (3,)
    assert np.all(np.isfinite(y))


# ---------------------------------------------------------------------------
# 4. Coherence metier
# ---------------------------------------------------------------------------


def test_les_predictions_sont_positives(model, scaler):
    y = _predict(model, scaler, list(range(405, 1504, 100)))
    assert np.all(y >= 0), f"Predictions negatives constatees : {y[y < 0]}"


def test_la_prediction_croit_avec_la_distance_en_tendance(model, scaler):
    """Correlation de rang sur le domaine d'entrainement.

    Voir SPEARMAN_MIN : le modele n'est pas strictement monotone, ce test
    verifie la tendance, qui est ce que le modele garantit reellement.
    """
    distances = list(range(405, 1504, 50))
    y = _predict(model, scaler, distances)
    rho = float(spearmanr(distances, y).statistic)
    assert rho >= SPEARMAN_MIN, (
        f"Correlation de rang distance/prediction = {rho:.4f}, "
        f"minimum attendu {SPEARMAN_MIN}"
    )


def test_les_extremes_du_domaine_sont_ordonnes(model, scaler):
    y_min, y_max = _predict(model, scaler, [405, 1503])
    assert y_max > y_min, (
        f"La prediction a 1503 km ({y_max:.4f}) n'est pas superieure "
        f"a celle a 405 km ({y_min:.4f})"
    )


# ---------------------------------------------------------------------------
# 5. Non-regression sur cas de reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("distance,expected", REFERENCE_CASES)
def test_non_regression_sur_cas_de_reference(model, scaler, distance, expected):
    y = float(_predict(model, scaler, [distance])[0])
    ecart = abs(y - expected)
    assert ecart <= REFERENCE_TOLERANCE_KG, (
        f"distance={distance} km : prediction {y:.4f} kg, reference {expected:.4f} kg, "
        f"ecart {ecart:.4f} > tolerance {REFERENCE_TOLERANCE_KG}"
    )


def test_le_modele_est_deterministe(model, scaler):
    """Deux appels identiques doivent rendre exactement la meme valeur."""
    a = _predict(model, scaler, [405, 800, 1200, 1503])
    b = _predict(model, scaler, [405, 800, 1200, 1503])
    np.testing.assert_array_equal(a, b)


# ---------------------------------------------------------------------------
# 6. Tracabilite
# ---------------------------------------------------------------------------


def test_le_metadata_est_complet(metadata):
    for key in (
        "model_version",
        "created_at",
        "commit_sha",
        "seed",
        "features",
        "estimator",
        "library_versions",
    ):
        assert key in metadata, f"Cle absente du metadata.json : {key}"
    assert metadata["library_versions"]["xgboost"], "Version xgboost non journalisee"
    assert metadata["library_versions"]["scikit-learn"], "Version scikit-learn non journalisee"


def test_les_features_du_metadata_correspondent_au_scaler(metadata, scaler):
    assert list(metadata["features"]) == list(scaler.feature_names_in_)
