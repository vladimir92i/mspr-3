"""Validation du modele CO2 ObRail avec porte de qualite.

Etape 3 de la chaine de livraison continue du modele (C13).

Ce script est une PORTE : il rend un code retour non nul si le modele
n'atteint pas les seuils de ml/thresholds.yaml, ou s'il regresse par rapport
au champion precedent. Sans cette capacite d'echec, l'etape ne serait pas une
validation mais un simple affichage.

Le jeu de test est celui fige par ml/train.py (out-dir/test_set.csv) : on
evalue exactement sur les lignes que l'entrainement n'a jamais vues, sans
dependre d'un re-decoupage qui pourrait deriver.

Codes retour :
  0 : tous les seuils sont respectes
  1 : au moins un seuil n'est pas atteint, ou regression vs champion
  2 : erreur d'execution (artefacts ou configuration absents)

Usage :
  python ml/evaluate.py --model-dir ml/artifacts --config ml/thresholds.yaml \
      --champion ml/champion/evaluation.json --report-dir ml/reports
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

TARGET = "emission"


def build_markdown(payload: dict) -> str:
    """Rapport lisible. Structure de titres sans saut de niveau, tableaux
    avec en-tetes, statut porte en toutes lettres et jamais par la couleur."""
    m = payload["metrics"]
    t = payload["thresholds"]
    lines = [
        "# Rapport d'evaluation du modele CO2 ObRail",
        "",
        f"- Version du modele : `{payload['model_version']}`",
        f"- Commit : `{payload['commit_sha']}`",
        f"- Date d'evaluation : {payload['evaluated_at']}",
        f"- Jeu de test : {payload['n_test_rows']} lignes",
        f"- **Verdict global : {payload['verdict']}**",
        "",
        "## Metriques mesurees",
        "",
        "| Metrique | Valeur mesuree | Seuil | Respecte |",
        "| :------- | -------------: | ----: | :------- |",
        f"| R2 | {m['r2']:.4f} | >= {t['r2_min']} | {payload['gates']['r2']} |",
        f"| MAE | {m['mae']:.4f} | <= {t['mae_max']} | {payload['gates']['mae']} |",
        f"| RMSE | {m['rmse']:.4f} | <= {t['rmse_max']} | {payload['gates']['rmse']} |",
        "",
        "## Non-regression",
        "",
    ]
    champ = payload["champion"]
    if champ["available"]:
        lines += [
            "| Element | Valeur |",
            "| :------ | -----: |",
            f"| R2 du champion | {champ['r2']:.4f} |",
            f"| R2 du challenger | {m['r2']:.4f} |",
            f"| Delta | {champ['delta']:+.4f} |",
            f"| Tolerance | -{t['regression_tolerance_r2']} |",
            "",
            f"Statut : {champ['status']}",
        ]
    else:
        lines += [
            "Aucun modele champion enregistre : la comparaison de non-regression",
            "n'a pas pu etre effectuee. Ce premier modele valide fera reference",
            "pour les executions suivantes.",
        ]
    lines += [
        "",
        "## Signature du modele",
        "",
        "| Element | Valeur |",
        "| :------ | :----- |",
        f"| Estimateur | `{payload['estimator']}` |",
        f"| Features attendues | {', '.join(payload['features'])} |",
        f"| Nombre de features | {payload['n_features']} |",
        "",
        "## Interpretation",
        "",
        payload["interpretation"],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validation du modele CO2 avec porte de qualite.")
    parser.add_argument("--model-dir", default="ml/artifacts")
    parser.add_argument("--config", default="ml/thresholds.yaml")
    parser.add_argument("--champion", default="ml/champion/evaluation.json")
    parser.add_argument("--report-dir", default="ml/reports")
    parser.add_argument(
        "--r2-min",
        type=float,
        default=None,
        help="Surcharge le seuil r2_min du fichier de configuration.",
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    config_path = Path(args.config)
    for p in (model_dir / "model_final.joblib", model_dir / "scaler.joblib",
              model_dir / "test_set.csv", model_dir / "metadata.json", config_path):
        if not p.exists():
            print(f"ERREUR : fichier requis introuvable : {p}", file=sys.stderr)
            return 2

    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))["model"]
    if args.r2_min is not None:
        print(f"Seuil r2_min surcharge en ligne de commande : {args.r2_min} (fichier : {cfg['r2_min']})")
        cfg["r2_min"] = args.r2_min

    metadata = json.loads((model_dir / "metadata.json").read_text(encoding="utf-8"))
    model = joblib.load(model_dir / "model_final.joblib")
    scaler = joblib.load(model_dir / "scaler.joblib")
    features = list(metadata["features"])

    test = pd.read_csv(model_dir / "test_set.csv")
    X_test = test[features]
    y_test = test[TARGET]

    y_pred = model.predict(scaler.transform(X_test))

    r2 = float(r2_score(y_test, y_pred))
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

    print(f"Jeu de test : {len(test)} lignes")
    print(f"R2   = {r2:.4f}  (seuil >= {cfg['r2_min']})")
    print(f"MAE  = {mae:.4f}  (seuil <= {cfg['mae_max']})")
    print(f"RMSE = {rmse:.4f}  (seuil <= {cfg['rmse_max']})")

    gates = {
        "r2": "OUI" if r2 >= cfg["r2_min"] else "NON",
        "mae": "OUI" if mae <= cfg["mae_max"] else "NON",
        "rmse": "OUI" if rmse <= cfg["rmse_max"] else "NON",
    }
    failures = [k for k, v in gates.items() if v == "NON"]

    # --- Non-regression vs champion ---------------------------------------
    champion_path = Path(args.champion)
    champion = {"available": False, "r2": None, "delta": None, "status": "NON APPLICABLE"}
    if champion_path.exists():
        try:
            champ_data = json.loads(champion_path.read_text(encoding="utf-8"))
            champ_r2 = float(champ_data["metrics"]["r2"])
            delta = r2 - champ_r2
            tol = float(cfg["regression_tolerance_r2"])
            regressed = delta < -tol
            champion = {
                "available": True,
                "r2": champ_r2,
                "delta": delta,
                "status": "REGRESSION DETECTEE" if regressed else "PAS DE REGRESSION",
            }
            print(
                f"Champion : R2={champ_r2:.4f} | challenger R2={r2:.4f} | "
                f"delta={delta:+.4f} | tolerance=-{tol} -> {champion['status']}"
            )
            if regressed:
                failures.append("non_regression")
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            print(f"AVERTISSEMENT : champion illisible ({e}), comparaison ignoree", file=sys.stderr)
    else:
        print(f"Aucun champion enregistre a {champion_path} : non-regression non evaluee")

    verdict = "ACCEPTE" if not failures else "REFUSE"

    if not failures:
        interpretation = (
            f"Le modele atteint un R2 de {r2:.4f} sur {len(test)} lignes de test jamais vues "
            f"a l'entrainement, au-dessus du seuil de {cfg['r2_min']}. L'erreur absolue moyenne "
            f"est de {mae:.4f} kg de CO2. Le modele est accepte pour empaquetage."
        )
    else:
        interpretation = (
            f"Le modele est refuse : {len(failures)} critere(s) non respecte(s) ({', '.join(failures)}). "
            f"Aucun empaquetage ni publication ne doit avoir lieu. Voir la procedure de "
            f"debogage dans docs/MLOPS_PIPELINE.md."
        )

    payload = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "model_version": metadata["model_version"],
        "commit_sha": metadata["commit_sha"],
        "seed": metadata["seed"],
        "n_test_rows": int(len(test)),
        "features": features,
        "n_features": len(features),
        "estimator": f"{metadata['estimator']['module']}.{metadata['estimator']['class']}",
        "metrics": {"r2": r2, "mae": mae, "rmse": rmse},
        "thresholds": {
            "r2_min": cfg["r2_min"],
            "mae_max": cfg["mae_max"],
            "rmse_max": cfg["rmse_max"],
            "regression_tolerance_r2": cfg["regression_tolerance_r2"],
        },
        "gates": gates,
        "champion": champion,
        "failures": failures,
        "verdict": verdict,
        "interpretation": interpretation,
    }

    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "evaluation.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (report_dir / "evaluation.md").write_text(build_markdown(payload), encoding="utf-8")
    print(f"Rapports ecrits : {report_dir}/evaluation.json et {report_dir}/evaluation.md")

    print("-" * 72)
    if not failures:
        print(f"RESULTAT : MODELE {verdict}")
        return 0
    print(f"RESULTAT : MODELE {verdict} - criteres en echec : {', '.join(failures)}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
