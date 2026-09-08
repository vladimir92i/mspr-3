"""Entrainement reproductible du modele CO2 ObRail.

Etape 2 de la chaine de livraison continue du modele (C13).

L'algorithme et les hyperparametres reproduisent a l'identique l'artefact
livre dans backend/app/services/ia/model_final.joblib, verifie par
introspection :
    xgboost.sklearn.XGBRegressor(n_estimators=100, random_state=42, verbosity=0)
    objective = reg:squarederror
    n_features_in_ = 1
avec en amont un sklearn.preprocessing.StandardScaler ajuste sur la seule
feature 'distance' (feature_names_in_ = ['distance']).

Ce script N'ECRASE PAS le modele servi par l'API : il ecrit dans --out-dir
(ml/artifacts par defaut). La promotion vers backend/app/services/ia/ est une
decision humaine, hors de cette chaine.

Reproductibilite :
  - la graine est fixee, journalisee et enregistree dans metadata.json ;
  - le scaler est ajuste UNIQUEMENT sur le jeu d'entrainement, ce qui evite
    toute fuite de donnees du jeu de test vers la normalisation ;
  - le jeu de test est ecrit sur disque pour que ml/evaluate.py soit evalue
    exactement sur les memes lignes, sans dependre d'un re-decoupage.

Codes retour :
  0 : entrainement termine, artefacts ecrits
  2 : erreur d'execution (donnees ou configuration absentes)

Usage :
  python ml/train.py --data data/dataset_final.csv --seed 42 --out-dir ml/artifacts
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
import yaml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

TARGET = "emission"


def _json_safe(value):
    """Rend une valeur serialisable en JSON STRICT.

    json.dumps accepte NaN par defaut, mais NaN n'existe pas dans la norme
    JSON : jq, JSON.parse et la plupart des parseurs le rejettent. Or
    XGBRegressor expose `missing=nan` parmi ses hyperparametres, et le
    metadata.json est relu par le workflow. On convertit donc NaN et Infinity
    en chaines explicites plutot que de produire un fichier illisible.
    """
    if isinstance(value, float):
        if np.isnan(value):
            return "NaN"
        if np.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value
    if isinstance(value, (int, str, bool, type(None))):
        return value
    return str(value)


def get_commit_sha() -> str:
    """SHA du commit courant, ou 'UNKNOWN' hors depot Git.

    On ne fabrique pas de valeur : si Git ne repond pas, le metadata porte
    explicitement UNKNOWN.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser(description="Entrainement du modele CO2 ObRail.")
    parser.add_argument("--data", default="data/dataset_final.csv")
    parser.add_argument("--config", default="ml/thresholds.yaml")
    parser.add_argument("--out-dir", default="ml/artifacts")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.30)
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    data_path = Path(args.data)
    config_path = Path(args.config)
    if not data_path.exists():
        print(f"ERREUR : jeu de donnees introuvable : {data_path}", file=sys.stderr)
        return 2
    if not config_path.exists():
        print(f"ERREUR : fichier de seuils introuvable : {config_path}", file=sys.stderr)
        return 2

    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    features = list(cfg["signature"]["features"])

    # --- Graine ------------------------------------------------------------
    np.random.seed(args.seed)
    print(f"Graine fixee : {args.seed}")

    # --- Donnees -----------------------------------------------------------
    df = pd.read_csv(data_path)
    missing = [c for c in features + [TARGET] if c not in df.columns]
    if missing:
        print(f"ERREUR : colonnes absentes du jeu de donnees : {missing}", file=sys.stderr)
        return 2

    X = df[features]
    y = df[TARGET]
    print(f"Donnees : {len(df)} lignes | features {features} | cible '{TARGET}'")

    # --- Split explicite ---------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed
    )
    print(f"Split train/test : {len(X_train)} / {len(X_test)} (test_size={args.test_size})")

    # --- Normalisation : ajustee sur le TRAIN uniquement -------------------
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print(f"Scaler ajuste sur le train : mean_={scaler.mean_} scale_={scaler.scale_}")

    # --- Entrainement ------------------------------------------------------
    model = XGBRegressor(
        n_estimators=args.n_estimators,
        random_state=args.seed,
        verbosity=0,
        objective="reg:squarederror",
    )
    model.fit(X_train_scaled, y_train)
    print(
        f"Modele entraine : {type(model).__name__} "
        f"n_estimators={args.n_estimators} random_state={args.seed} "
        f"n_features_in_={model.n_features_in_}"
    )

    # --- Sauvegarde --------------------------------------------------------
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, out_dir / "model_final.joblib")
    joblib.dump(scaler, out_dir / "scaler.joblib")
    joblib.dump(features, out_dir / "features.joblib")

    # Le jeu de test est fige pour que l'evaluation porte exactement sur les
    # memes lignes, independamment de toute logique de re-decoupage.
    test_set = X_test.copy()
    test_set[TARGET] = y_test
    test_set.to_csv(out_dir / "test_set.csv", index=False)

    now = datetime.now(timezone.utc)
    model_version = f"{now:%Y%m%d}-{get_commit_sha()[:7]}"
    metadata = {
        "model_version": model_version,
        "created_at": now.isoformat(),
        "commit_sha": get_commit_sha(),
        "seed": args.seed,
        "test_size": args.test_size,
        "n_rows_total": int(len(df)),
        "n_rows_train": int(len(X_train)),
        "n_rows_test": int(len(X_test)),
        "features": features,
        "n_features": len(features),
        "target": TARGET,
        "estimator": {
            "class": type(model).__name__,
            "module": type(model).__module__,
            "hyperparameters": {
                k: _json_safe(v) for k, v in model.get_params().items() if v is not None
            },
        },
        "scaler": {
            "class": type(scaler).__name__,
            "module": type(scaler).__module__,
            "mean_": scaler.mean_.tolist(),
            "scale_": scaler.scale_.tolist(),
            "feature_names_in_": list(getattr(scaler, "feature_names_in_", [])),
        },
        "library_versions": {
            "python": sys.version.split()[0],
            "scikit-learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "joblib": joblib.__version__,
        },
        "training_data": {
            "path": str(data_path),
            "rows": int(len(df)),
        },
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("-" * 72)
    print(f"Artefacts ecrits dans {out_dir}/ :")
    for name in ("model_final.joblib", "scaler.joblib", "features.joblib", "test_set.csv", "metadata.json"):
        p = out_dir / name
        print(f"  {name:22} {p.stat().st_size:>9} octets")
    print(f"Version du modele : {model_version}")
    print("RESULTAT : ENTRAINEMENT TERMINE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
