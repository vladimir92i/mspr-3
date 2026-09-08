"""Validation des donnees d'entrainement du modele CO2 ObRail.

Etape 1 de la chaine de livraison continue du modele (C13).

Choix technique : pandas + assertions explicites, PAS pandera.
Justification :
  1. pandera n'est pas dans backend/requirements.txt ; l'ajouter introduit une
     contrainte de compatibilite supplementaire avec pandas 3.0.2, version
     recente pour laquelle le support pandera n'est pas garanti.
  2. Le livrable attendu est un rapport JSON + un code retour : ces deux
     elements doivent etre ecrits a la main de toute facon, pandera ne les
     fournit pas dans ce format.
  3. Moins de dependances = moins de surface de panne en CI.
Le cout est une verification de schema ecrite explicitement, ce que fait
`check_schema` ci-dessous en une trentaine de lignes.

Codes retour :
  0 : toutes les regles bloquantes passent
  1 : au moins une regle bloquante echoue
  2 : erreur d'execution (fichier absent, YAML illisible)

Usage :
  python ml/data/validate_data.py \
      --data data/dataset_final.csv \
      --config ml/thresholds.yaml \
      --report ml/reports/data_validation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

# --------------------------------------------------------------------------
# Infrastructure de collecte des resultats
# --------------------------------------------------------------------------


class CheckResults:
    """Accumule le resultat de chaque regle sans interrompre l'execution.

    On execute TOUTES les regles avant de sortir : un rapport qui s'arrete a
    la premiere erreur oblige a relancer le pipeline autant de fois qu'il y a
    de defauts.
    """

    def __init__(self) -> None:
        self.checks: list[dict] = []

    def add(self, name: str, passed: bool, detail: str, blocking: bool = True) -> None:
        self.checks.append(
            {
                "check": name,
                "status": "PASS" if passed else ("FAIL" if blocking else "WARN"),
                "blocking": blocking,
                "detail": detail,
            }
        )

    @property
    def failed(self) -> list[dict]:
        return [c for c in self.checks if c["status"] == "FAIL"]

    @property
    def warnings(self) -> list[dict]:
        return [c for c in self.checks if c["status"] == "WARN"]

    @property
    def ok(self) -> bool:
        return not self.failed


# --------------------------------------------------------------------------
# Regles de validation
# --------------------------------------------------------------------------

_TYPE_FAMILIES = {
    "int": "i",
    "float": "f",
}


def check_schema(df: pd.DataFrame, schema: dict, res: CheckResults) -> None:
    """Colonnes attendues presentes, et types compatibles."""
    expected = set(schema)
    actual = set(df.columns)

    missing = sorted(expected - actual)
    res.add(
        "schema.colonnes_presentes",
        not missing,
        f"colonnes attendues : {sorted(expected)}"
        + (f" | MANQUANTES : {missing}" if missing else " | toutes presentes"),
    )

    extra = sorted(actual - expected)
    res.add(
        "schema.colonnes_inattendues",
        not extra,
        f"colonnes supplementaires : {extra}" if extra else "aucune colonne inattendue",
        blocking=False,
    )

    for col, expected_type in schema.items():
        if col not in df.columns:
            continue
        family = _TYPE_FAMILIES.get(expected_type)
        if family is None:
            res.add(f"schema.type.{col}", False, f"type attendu inconnu : {expected_type}")
            continue
        # Un entier est acceptable la ou un flottant est attendu, l'inverse non.
        actual_kind = df[col].dtype.kind
        accepted = (family,) if family == "i" else ("f", "i")
        passed = actual_kind in accepted
        res.add(
            f"schema.type.{col}",
            passed,
            f"attendu {expected_type} ({family}), constate {df[col].dtype} ({actual_kind})",
        )


def check_nulls(df: pd.DataFrame, critical: list[str], res: CheckResults) -> None:
    for col in critical:
        if col not in df.columns:
            res.add(f"nulls.{col}", False, "colonne absente, verification impossible")
            continue
        n = int(df[col].isnull().sum())
        res.add(f"nulls.{col}", n == 0, f"{n} valeur(s) nulle(s) sur {len(df)} lignes")


def check_bounds(df: pd.DataFrame, bounds: dict, res: CheckResults) -> None:
    for col, rules in bounds.items():
        if col not in df.columns:
            res.add(f"bounds.{col}", False, "colonne absente, verification impossible")
            continue
        serie = df[col]
        if "min_exclusive" in rules:
            limit = rules["min_exclusive"]
            n = int((serie <= limit).sum())
            res.add(
                f"bounds.{col}.strictement_superieur_a_{limit}",
                n == 0,
                f"{n} ligne(s) avec {col} <= {limit} | min constate = {serie.min()}",
            )
        if "min" in rules:
            limit = rules["min"]
            n = int((serie < limit).sum())
            res.add(
                f"bounds.{col}.min_{limit}",
                n == 0,
                f"{n} ligne(s) avec {col} < {limit} | min constate = {serie.min()}",
            )
        if "max" in rules:
            limit = rules["max"]
            n = int((serie > limit).sum())
            res.add(
                f"bounds.{col}.max_{limit}",
                n == 0,
                f"{n} ligne(s) avec {col} > {limit} | max constate = {serie.max()}",
            )


def check_duplicates(df: pd.DataFrame, max_ratio: float, res: CheckResults) -> None:
    n_dup = int(df.duplicated().sum())
    ratio = n_dup / len(df) if len(df) else 0.0
    res.add(
        "duplicates.lignes_completes",
        ratio <= max_ratio,
        f"{n_dup} doublon(s) exact(s) sur {len(df)} lignes "
        f"(ratio {ratio:.4f}, tolerance {max_ratio})",
    )


def check_volume(df: pd.DataFrame, min_rows: int, res: CheckResults) -> None:
    res.add(
        "volume.min_rows",
        len(df) >= min_rows,
        f"{len(df)} lignes, minimum requis {min_rows}",
    )


def check_target_variance(df: pd.DataFrame, res: CheckResults) -> None:
    """Une cible constante rend tout R2 non defini : on l'ecarte tot."""
    if "emission" not in df.columns:
        return
    n_unique = int(df["emission"].nunique())
    res.add(
        "target.variance",
        n_unique > 1,
        f"{n_unique} valeur(s) distincte(s) de emission",
    )


# --------------------------------------------------------------------------
# Point d'entree
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Validation des donnees d'entrainement CO2.")
    parser.add_argument("--data", default="data/dataset_final.csv")
    parser.add_argument("--config", default="ml/thresholds.yaml")
    parser.add_argument("--report", default="ml/reports/data_validation.json")
    args = parser.parse_args()

    data_path = Path(args.data)
    config_path = Path(args.config)

    if not data_path.exists():
        print(f"ERREUR : jeu de donnees introuvable : {data_path}", file=sys.stderr)
        return 2
    if not config_path.exists():
        print(f"ERREUR : fichier de seuils introuvable : {config_path}", file=sys.stderr)
        return 2

    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))["data"]
    df = pd.read_csv(data_path)

    print(f"Jeu de donnees : {data_path} | {df.shape[0]} lignes x {df.shape[1]} colonnes")

    res = CheckResults()
    check_schema(df, cfg["schema"], res)
    check_nulls(df, cfg["critical_columns"], res)
    check_bounds(df, cfg["bounds"], res)
    check_duplicates(df, float(cfg["max_duplicate_ratio"]), res)
    check_volume(df, int(cfg["min_rows"]), res)
    check_target_variance(df, res)

    print("-" * 72)
    for c in res.checks:
        print(f"[{c['status']:4}] {c['check']:45} {c['detail']}")
    print("-" * 72)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(data_path),
        "rows": int(df.shape[0]),
        "columns": list(df.columns),
        "passed": res.ok,
        "n_checks": len(res.checks),
        "n_failed": len(res.failed),
        "n_warnings": len(res.warnings),
        "checks": res.checks,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Rapport ecrit : {report_path}")

    if res.ok:
        print(f"RESULTAT : VALIDATION REUSSIE ({len(res.warnings)} avertissement(s))")
        return 0

    print(f"RESULTAT : VALIDATION ECHOUEE - {len(res.failed)} regle(s) bloquante(s)", file=sys.stderr)
    for c in res.failed:
        print(f"  - {c['check']} : {c['detail']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
