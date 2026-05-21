#!/usr/bin/env python3
"""Recreate exploratory Random Forest predictive models for Tables 16-17.

This script rebuilds complete-case modelling tables from the released
text-level index files, merges corpus metadata for the target labels, and
evaluates Random Forest classifiers against a most-frequent-class baseline.

Implementation settings:
- scikit-learn RandomForestClassifier
- n_estimators=100
- random_state=42
- other Random Forest hyperparameters left at scikit-learn defaults
- StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
- no hyperparameter tuning
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate


RANDOM_STATE = 42
N_SPLITS = 5
N_ESTIMATORS = 100

CORPORA = {
    "COREFL": {
        "slug": "corefl",
        "metadata": "data_filtered/corefl_v2_filtered.csv",
        "metadata_id": "text_id",
        "target": "cefr",
        "levels": ("intra", "intersent", "interpara"),
    },
    "EFCAMDAT": {
        "slug": "efcamdat",
        "metadata": "data_filtered/efcamdat_v2_filtered.csv",
        "metadata_id": "writing_id",
        "target": "cefr",
        "levels": ("intra", "intersent"),
    },
    "GiG": {
        "slug": "gig",
        "metadata": "data_filtered/gig_v2_filtered.csv",
        "metadata_id": "text_id",
        "target": "year_group",
        "levels": ("intra", "intersent", "interpara"),
    },
}

LEVEL_DIRS = {
    "intra": "intra_sentential",
    "intersent": "inter_sentential",
    "interpara": "inter_paragraph",
}

LEVEL_LABELS = {
    "intra": "Intra-sentential only",
    "intersent": "Inter-sentential only",
    "interpara": "Inter-paragraph only",
    "all": "All available",
}

TABLE16_FEATURE_SETS = {
    "Totals": "totals",
    "Macro": "macro",
    "All normalized": "all_normalized",
}


def normalize_id(corpus_slug: str, value: object) -> str:
    text_id = str(value).strip().lower()
    if corpus_slug == "efcamdat" and not text_id.startswith("efcamdat_"):
        return f"efcamdat_{text_id}"
    if corpus_slug == "gig" and not text_id.startswith("gig_"):
        return f"gig_{text_id}"
    return text_id


def read_level_indices(paper_outputs: Path, corpus_slug: str, level: str) -> pd.DataFrame:
    path = (
        paper_outputs
        / "text_level_indices"
        / LEVEL_DIRS[level]
        / f"{corpus_slug}_{level}_text_indices.csv"
    )
    df = pd.read_csv(path)
    df["model_id"] = df["text_id"].map(lambda value: normalize_id(corpus_slug, value))

    feature_cols = [col for col in df.columns if col.endswith("_per_1000")]
    keep = ["model_id"] + feature_cols
    df = df[keep].copy()
    df = df.rename(columns={col: f"{level}_{col}" for col in feature_cols})
    return df


def read_metadata(repo_root: Path, corpus_name: str, corpus_cfg: dict[str, object]) -> pd.DataFrame:
    metadata_path = repo_root / str(corpus_cfg["metadata"])
    id_col = str(corpus_cfg["metadata_id"])
    target = str(corpus_cfg["target"])
    slug = str(corpus_cfg["slug"])

    metadata = pd.read_csv(metadata_path, dtype=str, usecols=[id_col, target])
    metadata["model_id"] = metadata[id_col].map(lambda value: normalize_id(slug, value))
    metadata = metadata[["model_id", target]].dropna()
    metadata = metadata.rename(columns={target: "target"})
    metadata["corpus"] = corpus_name
    return metadata


def build_modeling_table(
    repo_root: Path, paper_outputs: Path, corpus_name: str, corpus_cfg: dict[str, object]
) -> pd.DataFrame:
    slug = str(corpus_cfg["slug"])
    levels = tuple(corpus_cfg["levels"])

    table: pd.DataFrame | None = None
    for level in levels:
        level_df = read_level_indices(paper_outputs, slug, level)
        table = level_df if table is None else table.merge(level_df, on="model_id", how="inner")

    if table is None:
        raise ValueError(f"No level index files configured for {corpus_name}")

    metadata = read_metadata(repo_root, corpus_name, corpus_cfg)
    table = table.merge(metadata, on="model_id", how="inner")
    table = table.sort_values("model_id").reset_index(drop=True)
    return table


def columns_for_feature_set(table: pd.DataFrame, feature_set: str, levels: tuple[str, ...]) -> list[str]:
    feature_cols = [col for col in table.columns if col.endswith("_per_1000")]

    if feature_set == "totals":
        cols = [f"{level}_detected_cases_per_1000" for level in levels]
        return [col for col in cols if col in table.columns]

    if feature_set == "macro":
        return [col for col in feature_cols if "_macro_" in col]

    if feature_set == "all_normalized":
        return feature_cols

    if feature_set in LEVEL_DIRS:
        return [col for col in feature_cols if col.startswith(f"{feature_set}_")]

    raise ValueError(f"Unknown feature set: {feature_set}")


def remove_zero_variance_features(table: pd.DataFrame, cols: list[str]) -> list[str]:
    nonconstant = []
    for col in cols:
        values = pd.to_numeric(table[col], errors="coerce").fillna(0)
        if values.nunique(dropna=False) > 1:
            nonconstant.append(col)
    return nonconstant


def evaluate_feature_set(table: pd.DataFrame, cols: list[str]) -> dict[str, float]:
    X = table[cols].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy()
    y = table["target"].astype(str).to_numpy()

    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    scoring = {
        "macro_f1": "f1_macro",
        "balanced_accuracy": "balanced_accuracy",
        "accuracy": "accuracy",
    }

    baseline = DummyClassifier(strategy="most_frequent")
    rf = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )

    baseline_scores = cross_validate(baseline, X, y, cv=cv, scoring=scoring, n_jobs=1)
    rf_scores = cross_validate(rf, X, y, cv=cv, scoring=scoring, n_jobs=1)

    return {
        "baseline_macro_f1": float(np.mean(baseline_scores["test_macro_f1"])),
        "baseline_balanced_accuracy": float(np.mean(baseline_scores["test_balanced_accuracy"])),
        "baseline_accuracy": float(np.mean(baseline_scores["test_accuracy"])),
        "rf_macro_f1": float(np.mean(rf_scores["test_macro_f1"])),
        "rf_macro_f1_sd": float(np.std(rf_scores["test_macro_f1"], ddof=1)),
        "rf_balanced_accuracy": float(np.mean(rf_scores["test_balanced_accuracy"])),
        "rf_balanced_accuracy_sd": float(np.std(rf_scores["test_balanced_accuracy"], ddof=1)),
        "rf_accuracy": float(np.mean(rf_scores["test_accuracy"])),
        "rf_accuracy_sd": float(np.std(rf_scores["test_accuracy"], ddof=1)),
    }


def round_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "baseline_macro_f1",
        "baseline_balanced_accuracy",
        "baseline_accuracy",
        "rf_macro_f1",
        "rf_macro_f1_sd",
        "rf_balanced_accuracy",
        "rf_balanced_accuracy_sd",
        "rf_accuracy",
        "rf_accuracy_sd",
    ]
    out = df.copy()
    for col in metric_cols:
        if col in out.columns:
            out[col] = out[col].round(3)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--paper-outputs",
        type=Path,
        default=Path("../conjunction_analysis_reproducibility_release/paper_outputs"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("outputs/recreated_predictive_models"),
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    paper_outputs = args.paper_outputs.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    table16_rows: list[dict[str, object]] = []
    table17_rows: list[dict[str, object]] = []

    for corpus_name, corpus_cfg in CORPORA.items():
        levels = tuple(corpus_cfg["levels"])
        table = build_modeling_table(repo_root, paper_outputs, corpus_name, corpus_cfg)
        table.to_csv(out_dir / f"{corpus_cfg['slug']}_modeling_table_complete_cases.csv", index=False)

        n = len(table)
        n_classes = table["target"].nunique()
        print(f"Running {corpus_name}: n={n}, classes={n_classes}", flush=True)

        for label, feature_set in TABLE16_FEATURE_SETS.items():
            cols = remove_zero_variance_features(table, columns_for_feature_set(table, feature_set, levels))
            print(f"  Table 16 {label}: {len(cols)} features", flush=True)
            metrics = evaluate_feature_set(table, cols)
            table16_rows.append(
                {
                    "corpus": corpus_name,
                    "feature_set": label,
                    "n": n,
                    "n_classes": n_classes,
                    "n_features": len(cols),
                    **metrics,
                }
            )

        for level in levels:
            cols = remove_zero_variance_features(table, columns_for_feature_set(table, level, levels))
            print(f"  Table 17 {LEVEL_LABELS[level]}: {len(cols)} features", flush=True)
            metrics = evaluate_feature_set(table, cols)
            table17_rows.append(
                {
                    "corpus": corpus_name,
                    "feature_level": LEVEL_LABELS[level],
                    "n": n,
                    "n_classes": n_classes,
                    "n_features": len(cols),
                    **metrics,
                }
            )

        cols = remove_zero_variance_features(table, columns_for_feature_set(table, "all_normalized", levels))
        print(f"  Table 17 {LEVEL_LABELS['all']}: {len(cols)} features", flush=True)
        metrics = evaluate_feature_set(table, cols)
        table17_rows.append(
            {
                "corpus": corpus_name,
                "feature_level": LEVEL_LABELS["all"],
                "n": n,
                "n_classes": n_classes,
                "n_features": len(cols),
                **metrics,
            }
        )

    table16 = round_metrics(pd.DataFrame(table16_rows))
    table17 = round_metrics(pd.DataFrame(table17_rows))

    table16.to_csv(out_dir / "table16_recreated_baseline_vs_random_forest.csv", index=False)
    table17.to_csv(out_dir / "table17_recreated_level_ablation_random_forest.csv", index=False)

    print(f"Saved recreated outputs to {out_dir}")
    print("\nTable 16 recreated:")
    print(table16.to_string(index=False))
    print("\nTable 17 recreated:")
    print(table17.to_string(index=False))


if __name__ == "__main__":
    main()
