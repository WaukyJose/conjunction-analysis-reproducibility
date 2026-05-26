#!/usr/bin/env python3
"""Corrected zero-inclusive Random Forest analysis for Section 4.5."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import hashlib
import json
import time

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate


ROOT = Path(__file__).resolve().parents[2]
PRED_DIR = ROOT / "outputs/predictive_analysis_corrected"
AUDIT_DIR = ROOT / "outputs/ml_audit_corrected"

SOURCES = {
    "intra": ROOT / "outputs/v2_intrasentential_full/v2_intrasentential_full_supported_text_indices.csv",
    "intersent": ROOT / "outputs/v2_intersentential_full/v2_intersentential_full_supported_text_indices.csv",
    "interpara": ROOT / "outputs/v2_interparagraph_full/v2_interparagraph_full_supported_text_indices.csv",
}

RANDOM_STATE = 42
N_SPLITS = 5
N_ESTIMATORS = 100

GROUP_ORDERS = {
    "COREFL": ["A1", "A2", "B1", "B2", "C1", "C2"],
    "EFCAMDAT": ["A1", "A2", "B1", "B2", "C1"],
    "GiG": ["2", "4", "6", "9", "11"],
}

CORPUS_LEVELS = {
    "COREFL": ["intra", "intersent", "interpara"],
    "EFCAMDAT": ["intra", "intersent"],
    "GiG": ["intra", "intersent", "interpara"],
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


@dataclass
class EvaluationResult:
    corpus: str
    model_family: str
    feature_scope: str
    n_texts: int
    n_classes: int
    n_features: int
    class_counts: str
    baseline_macro_f1: float
    baseline_macro_f1_sd: float
    baseline_balanced_accuracy: float
    baseline_balanced_accuracy_sd: float
    baseline_accuracy: float
    baseline_accuracy_sd: float
    rf_macro_f1: float
    rf_macro_f1_sd: float
    rf_balanced_accuracy: float
    rf_balanced_accuracy_sd: float
    rf_accuracy: float
    rf_accuracy_sd: float


def normalize_model_id(corpus: str, value: object) -> str:
    text_id = str(value).strip().lower()
    if corpus == "EFCAMDAT" and not text_id.startswith("efcamdat_"):
        return f"efcamdat_{text_id}"
    if corpus == "GiG" and not text_id.startswith("gig_"):
        return f"gig_{text_id}"
    return text_id


def read_sources() -> dict[str, pd.DataFrame]:
    frames = {}
    for level, path in SOURCES.items():
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path, low_memory=False)
        df["corpus"] = df["corpus"].astype(str)
        df["target"] = df["group"].astype(str)
        df["model_id"] = [
            normalize_model_id(corpus, text_id)
            for corpus, text_id in zip(df["corpus"], df["text_id"])
        ]
        frames[level] = df
    return frames


def add_intra_macro_totals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    pairs = {
        "supported_intra_extension_per_1000": [
            "supported_intra_paratactic_extension_per_1000",
            "supported_intra_hypotactic_extension_per_1000",
        ],
        "supported_intra_enhancement_per_1000": [
            "supported_intra_paratactic_enhancement_per_1000",
            "supported_intra_hypotactic_enhancement_per_1000",
        ],
        "supported_intra_elaboration_per_1000": [
            "supported_intra_paratactic_elaboration_per_1000",
            "supported_intra_hypotactic_elaboration_per_1000",
        ],
        "supported_intra_parataxis_per_1000": [
            "supported_intra_paratactic_elaboration_per_1000",
            "supported_intra_paratactic_extension_per_1000",
            "supported_intra_paratactic_enhancement_per_1000",
        ],
        "supported_intra_hypotaxis_per_1000": [
            "supported_intra_hypotactic_elaboration_per_1000",
            "supported_intra_hypotactic_extension_per_1000",
            "supported_intra_hypotactic_enhancement_per_1000",
        ],
    }
    for new_col, cols in pairs.items():
        missing = [col for col in cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing intra macro source columns for {new_col}: {missing}")
        df[new_col] = df[cols].sum(axis=1)
    return df


def feature_columns_for_level(df: pd.DataFrame, level: str) -> dict[str, list[str]]:
    if level == "intra":
        total = ["supported_intra_total_per_1000"]
        macro = [
            "supported_intra_extension_per_1000",
            "supported_intra_enhancement_per_1000",
            "supported_intra_elaboration_per_1000",
        ]
        exclude = {
            "intra_sentential_per_1000_words",
        }
        all_norm = [
            col
            for col in df.columns
            if col.endswith("_per_1000")
            and col not in exclude
            and not col.endswith("_per_eligible_paragraph_start")
        ]
    elif level == "intersent":
        total = ["supported_inter_sentential_total_per_1000"]
        macro = [
            "supported_inter_sentential_extension_per_1000",
            "supported_inter_sentential_enhancement_per_1000",
            "supported_inter_sentential_elaboration_per_1000",
        ]
        all_norm = [col for col in df.columns if col.startswith("supported_inter_sentential_") and col.endswith("_per_1000")]
    elif level == "interpara":
        total = ["supported_interparagraph_total_per_1000"]
        macro = [
            "supported_interparagraph_extension_per_1000",
            "supported_interparagraph_enhancement_per_1000",
            "supported_interparagraph_elaboration_per_1000",
        ]
        all_norm = [
            col
            for col in df.columns
            if col.startswith("supported_interparagraph_") and col.endswith("_per_1000")
        ]
    else:
        raise ValueError(level)

    for cols in [total, macro, all_norm]:
        missing = sorted(set(cols) - set(df.columns))
        if missing:
            raise ValueError(f"Missing {level} feature columns: {missing}")

    return {
        "totals": total,
        "macro": macro,
        "all_normalized": sorted(set(all_norm)),
    }


def build_level_tables(frames: dict[str, pd.DataFrame]) -> tuple[dict[tuple[str, str], pd.DataFrame], dict[tuple[str, str], dict[str, list[str]]]]:
    frames = frames.copy()
    frames["intra"] = add_intra_macro_totals(frames["intra"])

    tables = {}
    feature_sets = {}
    for level, df in frames.items():
        features = feature_columns_for_level(df, level)
        all_feature_cols = sorted(set().union(*features.values()))
        for corpus in GROUP_ORDERS:
            if level == "interpara" and corpus == "EFCAMDAT":
                continue
            sub = df[df["corpus"].eq(corpus)].copy()
            keep = ["model_id", "corpus", "target"] + all_feature_cols
            sub = sub[keep].copy()
            for col in all_feature_cols:
                sub[col] = pd.to_numeric(sub[col], errors="coerce").fillna(0.0)
            sub = sub.rename(columns={col: f"{level}__{col}" for col in all_feature_cols})
            renamed_features = {
                name: [f"{level}__{col}" for col in cols]
                for name, cols in features.items()
            }
            tables[(corpus, level)] = sub
            feature_sets[(corpus, level)] = renamed_features
    return tables, feature_sets


def merge_levels(corpus: str, levels: list[str], tables: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for level in levels:
        level_table = tables[(corpus, level)].copy()
        if merged is None:
            merged = level_table
        else:
            feature_cols = [col for col in level_table.columns if col not in {"model_id", "corpus", "target"}]
            merged = merged.merge(
                level_table[["model_id"] + feature_cols],
                on="model_id",
                how="inner",
                validate="one_to_one",
            )
    if merged is None:
        raise ValueError(f"No levels to merge for {corpus}")
    return merged.sort_values("model_id").reset_index(drop=True)


def class_counts_string(y: pd.Series) -> str:
    order = GROUP_ORDERS[y.name] if y.name in GROUP_ORDERS else sorted(y.unique())
    counts = y.value_counts().to_dict()
    return "; ".join(f"{label}:{counts.get(label, 0)}" for label in order if label in counts)


def remove_zero_variance(table: pd.DataFrame, cols: list[str]) -> list[str]:
    kept = []
    for col in cols:
        values = pd.to_numeric(table[col], errors="coerce").fillna(0.0)
        if values.nunique(dropna=False) > 1:
            kept.append(col)
    return kept


def evaluate(table: pd.DataFrame, cols: list[str], corpus: str, model_family: str, feature_scope: str) -> tuple[EvaluationResult, pd.DataFrame]:
    cols = remove_zero_variance(table, cols)
    if not cols:
        raise ValueError(f"No nonconstant features for {corpus} {feature_scope}")

    X = table[cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    y_series = table["target"].astype(str)
    y_series.name = corpus
    y = y_series.to_numpy()

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

    rf_full = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    rf_full.fit(X, y)
    importances = pd.DataFrame(
        {
            "corpus": corpus,
            "model_family": model_family,
            "feature_scope": feature_scope,
            "feature": cols,
            "importance": rf_full.feature_importances_,
        }
    ).sort_values(["corpus", "model_family", "feature_scope", "importance"], ascending=[True, True, True, False])

    def mean_score(scores: dict[str, np.ndarray], metric: str) -> float:
        return float(np.mean(scores[f"test_{metric}"]))

    def sd_score(scores: dict[str, np.ndarray], metric: str) -> float:
        return float(np.std(scores[f"test_{metric}"], ddof=1))

    result = EvaluationResult(
        corpus=corpus,
        model_family=model_family,
        feature_scope=feature_scope,
        n_texts=int(len(table)),
        n_classes=int(y_series.nunique()),
        n_features=int(len(cols)),
        class_counts=class_counts_string(y_series),
        baseline_macro_f1=mean_score(baseline_scores, "macro_f1"),
        baseline_macro_f1_sd=sd_score(baseline_scores, "macro_f1"),
        baseline_balanced_accuracy=mean_score(baseline_scores, "balanced_accuracy"),
        baseline_balanced_accuracy_sd=sd_score(baseline_scores, "balanced_accuracy"),
        baseline_accuracy=mean_score(baseline_scores, "accuracy"),
        baseline_accuracy_sd=sd_score(baseline_scores, "accuracy"),
        rf_macro_f1=mean_score(rf_scores, "macro_f1"),
        rf_macro_f1_sd=sd_score(rf_scores, "macro_f1"),
        rf_balanced_accuracy=mean_score(rf_scores, "balanced_accuracy"),
        rf_balanced_accuracy_sd=sd_score(rf_scores, "balanced_accuracy"),
        rf_accuracy=mean_score(rf_scores, "accuracy"),
        rf_accuracy_sd=sd_score(rf_scores, "accuracy"),
    )
    return result, importances


def result_to_dict(result: EvaluationResult) -> dict[str, object]:
    return result.__dict__.copy()


def build_zero_row_audit(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    total_cols = {
        "intra": "supported_intra_total_raw",
        "intersent": "supported_inter_sentential_total_raw",
        "interpara": "supported_interparagraph_total_raw",
    }
    rows = []
    for level, df in frames.items():
        total_col = total_cols[level]
        for corpus, sub in df.groupby("corpus"):
            rows.append(
                {
                    "corpus": corpus,
                    "level": level,
                    "rows": int(len(sub)),
                    "zero_rows": int(sub[total_col].eq(0).sum()),
                    "zero_row_proportion": float(sub[total_col].eq(0).mean()),
                    "total_supported_tokens": int(sub[total_col].sum()),
                }
            )
    return pd.DataFrame(rows)


def write_summary(
    table16: pd.DataFrame,
    table17: pd.DataFrame,
    validation: pd.DataFrame,
    previous_table16_path: Path,
    previous_table17_path: Path,
) -> None:
    lines = [
        "# Corrected Section 4.5 Predictive Analysis",
        "",
        "This rerun uses only the corrected supported zero-inclusive text-index exports:",
        "",
    ]
    lines += [f"- `{path.relative_to(ROOT)}`" for path in SOURCES.values()]
    lines += [
        "",
        "No parser pipelines, descriptive statistics, inferential statistics, manuscript figures, SHAP/LIME, or Random Forest explainability workflows were rerun.",
        "",
        "## Preprocessing Impact",
        "",
        "The corrected workflow retains zero-density text rows instead of restricting models to detection-positive or complete sparse rows. This substantially increases the modeling sample for intra- and inter-sentential ablations, and it makes inter-paragraph models use all paragraph-eligible rows rather than only texts with detected paragraph-initial markers. As a result, the models are more conservative: they must distinguish developmental groups from the full analytic distribution, including texts where no supported marker was observed.",
        "",
        "For COREFL and GiG, inter-paragraph features are only available for paragraph-eligible texts with explicit paragraph boundaries. EFCAMDAT remains excluded from inter-paragraph features, as in the corrected Section 4.4 analyses.",
        "",
        "## Directional Comparison",
        "",
    ]

    if previous_table16_path.exists():
        old16 = pd.read_csv(previous_table16_path)
        new16 = table16.rename(columns={"feature_set": "feature_set"})
        comparable = old16.merge(
            new16,
            on=["corpus", "feature_set"],
            suffixes=("_old_sparse", "_corrected"),
        )
        if not comparable.empty:
            comparable["macro_f1_delta"] = comparable["rf_macro_f1_corrected"] - comparable["rf_macro_f1_old_sparse"]
            lines.append("Compared with the prior recreated sparse/complete-case Table 16, corrected macro-F1 changes are:")
            lines.append("")
            lines.append(comparable[["corpus", "feature_set", "rf_macro_f1_old_sparse", "rf_macro_f1_corrected", "macro_f1_delta"]].to_markdown(index=False, floatfmt=".3f"))
            lines.append("")

    if previous_table17_path.exists():
        old17 = pd.read_csv(previous_table17_path)
        comparable = old17.merge(
            table17,
            on=["corpus", "feature_level"],
            suffixes=("_old_sparse", "_corrected"),
        )
        if not comparable.empty:
            comparable["macro_f1_delta"] = comparable["rf_macro_f1_corrected"] - comparable["rf_macro_f1_old_sparse"]
            lines.append("Compared with the prior recreated sparse/complete-case Table 17, corrected level-ablation macro-F1 changes are:")
            lines.append("")
            lines.append(comparable[["corpus", "feature_level", "rf_macro_f1_old_sparse", "rf_macro_f1_corrected", "macro_f1_delta"]].to_markdown(index=False, floatfmt=".3f"))
            lines.append("")

    best_by_corpus = (
        table17.sort_values(["corpus", "rf_macro_f1"], ascending=[True, False])
        .groupby("corpus")
        .head(1)
        [["corpus", "feature_level", "rf_macro_f1", "rf_balanced_accuracy", "rf_accuracy"]]
    )
    lines += [
        "## Strongest Discourse-Level Signal",
        "",
        best_by_corpus.to_markdown(index=False, floatfmt=".3f"),
        "",
        "The strongest level-specific signal should be interpreted corpus by corpus, not as a general hierarchy of discourse levels. In the corrected run, all available features are not always better than individual discourse-level ablations, which is consistent with the exploratory status of Section 4.5.",
        "",
        "## Interpretation",
        "",
        "The original manuscript interpretation remains directionally valid only in the broad sense that conjunction-based indices contain some developmental signal above a most-frequent-class baseline, especially in larger corpora. However, the corrected zero-inclusive workflow requires moderation: performance is generally more conservative because absence of supported markers is now part of the modeled distribution, and inter-paragraph results are constrained to paragraph-eligible texts. Claims should therefore avoid implying robust predictive adequacy or stable discourse-level superiority.",
        "",
        "## Validation Snapshot",
        "",
        validation.to_markdown(index=False),
        "",
    ]
    (PRED_DIR / "predictive_summary_corrected.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    start = time.time()
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    frames = read_sources()
    tables, feature_sets = build_level_tables(frames)

    modeling_tables = {}
    for corpus, levels in CORPUS_LEVELS.items():
        for level in levels:
            modeling_tables[(corpus, level)] = tables[(corpus, level)]
        modeling_tables[(corpus, "all")] = merge_levels(corpus, levels, tables)

    for (corpus, scope), table in modeling_tables.items():
        table.to_csv(PRED_DIR / f"{corpus.lower()}_{scope}_feature_matrix.csv", index=False)

    corpus_group_counts = []
    for (corpus, scope), table in modeling_tables.items():
        counts = table["target"].value_counts().rename_axis("group").reset_index(name="n")
        counts.insert(0, "feature_scope", scope)
        counts.insert(0, "corpus", corpus)
        corpus_group_counts.append(counts)
    pd.concat(corpus_group_counts, ignore_index=True).to_csv(AUDIT_DIR / "corpus_group_counts.csv", index=False)

    zero_audit = build_zero_row_audit(frames)
    zero_audit.to_csv(AUDIT_DIR / "zero_row_proportions.csv", index=False)

    missing_rows = []
    feature_inventory_rows = []
    feature_count_rows = []
    all_results: list[EvaluationResult] = []
    all_importances = []

    for (corpus, scope), table in modeling_tables.items():
        feature_cols = [col for col in table.columns if col not in {"model_id", "corpus", "target"}]
        missing_rows.append(
            {
                "corpus": corpus,
                "feature_scope": scope,
                "n_rows": int(len(table)),
                "missing_target": int(table["target"].isna().sum()),
                "missing_feature_values_before_model_fill": int(table[feature_cols].isna().sum().sum()),
            }
        )
        for feature in feature_cols:
            feature_inventory_rows.append(
                {
                    "corpus": corpus,
                    "feature_scope": scope,
                    "feature": feature,
                }
            )

    # Table 16 uses all levels available for each corpus.
    for corpus in GROUP_ORDERS:
        table = modeling_tables[(corpus, "all")]
        levels = CORPUS_LEVELS[corpus]
        for label, feature_set_name in TABLE16_FEATURE_SETS.items():
            cols = []
            for level in levels:
                cols.extend(feature_sets[(corpus, level)][feature_set_name])
            cols = [col for col in cols if col in table.columns]
            feature_count_rows.append(
                {
                    "corpus": corpus,
                    "table": "Table 16",
                    "feature_scope": label,
                    "n_features_before_zero_variance_filter": len(cols),
                    "n_features_after_zero_variance_filter": len(remove_zero_variance(table, cols)),
                    "n_texts": int(len(table)),
                }
            )
            print(f"Table 16 {corpus} {label}: n={len(table)} features={len(cols)}", flush=True)
            result, importances = evaluate(table, cols, corpus, "Table 16", label)
            all_results.append(result)
            all_importances.append(importances)

    # Table 17 level ablations.
    for corpus, levels in CORPUS_LEVELS.items():
        for level in levels:
            table = modeling_tables[(corpus, level)]
            cols = feature_sets[(corpus, level)]["all_normalized"]
            feature_count_rows.append(
                {
                    "corpus": corpus,
                    "table": "Table 17",
                    "feature_scope": LEVEL_LABELS[level],
                    "n_features_before_zero_variance_filter": len(cols),
                    "n_features_after_zero_variance_filter": len(remove_zero_variance(table, cols)),
                    "n_texts": int(len(table)),
                }
            )
            print(f"Table 17 {corpus} {LEVEL_LABELS[level]}: n={len(table)} features={len(cols)}", flush=True)
            result, importances = evaluate(table, cols, corpus, "Table 17", LEVEL_LABELS[level])
            all_results.append(result)
            all_importances.append(importances)

        table = modeling_tables[(corpus, "all")]
        cols = [col for col in table.columns if col not in {"model_id", "corpus", "target"}]
        feature_count_rows.append(
            {
                "corpus": corpus,
                "table": "Table 17",
                "feature_scope": LEVEL_LABELS["all"],
                "n_features_before_zero_variance_filter": len(cols),
                "n_features_after_zero_variance_filter": len(remove_zero_variance(table, cols)),
                "n_texts": int(len(table)),
            }
        )
        print(f"Table 17 {corpus} {LEVEL_LABELS['all']}: n={len(table)} features={len(cols)}", flush=True)
        result, importances = evaluate(table, cols, corpus, "Table 17", LEVEL_LABELS["all"])
        all_results.append(result)
        all_importances.append(importances)

    metrics = pd.DataFrame([result_to_dict(result) for result in all_results])
    metric_cols = [col for col in metrics.columns if col.startswith("baseline_") or col.startswith("rf_")]
    rounded_metrics = metrics.copy()
    rounded_metrics[metric_cols] = rounded_metrics[metric_cols].round(3)

    table16 = rounded_metrics[rounded_metrics["model_family"].eq("Table 16")].copy()
    table16 = table16.rename(columns={"feature_scope": "feature_set"})
    table16 = table16.drop(columns=["model_family"])
    table17 = rounded_metrics[rounded_metrics["model_family"].eq("Table 17")].copy()
    table17 = table17.rename(columns={"feature_scope": "feature_level"})
    table17 = table17.drop(columns=["model_family"])

    table16.to_csv(PRED_DIR / "table16_corrected.csv", index=False)
    table17.to_csv(PRED_DIR / "table17_corrected.csv", index=False)
    rounded_metrics.to_csv(PRED_DIR / "rf_metrics_all_models.csv", index=False)
    pd.concat(all_importances, ignore_index=True).to_csv(PRED_DIR / "rf_feature_importances.csv", index=False)

    pd.DataFrame(feature_count_rows).to_csv(AUDIT_DIR / "feature_counts_by_model.csv", index=False)
    pd.DataFrame(missing_rows).to_csv(AUDIT_DIR / "missing_value_audit.csv", index=False)
    pd.DataFrame(feature_inventory_rows).to_csv(AUDIT_DIR / "feature_name_inventory.csv", index=False)

    model_config = pd.DataFrame(
        [
            {
                "random_state": RANDOM_STATE,
                "n_splits": N_SPLITS,
                "n_estimators": N_ESTIMATORS,
                "classifier": "sklearn.ensemble.RandomForestClassifier",
                "baseline": "sklearn.dummy.DummyClassifier(strategy='most_frequent')",
                "cv": "StratifiedKFold(shuffle=True)",
                "zero_rows": "retained",
                "feature_values_missing_fill": 0,
                "parser_rerun": "no",
            }
        ]
    )
    model_config.to_csv(AUDIT_DIR / "model_configurations.csv", index=False)

    validation = pd.DataFrame(
        [
            {
                "source_level": level,
                "source_file": str(path.relative_to(ROOT)),
                "rows": int(len(frames[level])),
                "corpora": ", ".join(sorted(frames[level]["corpus"].unique())),
            }
            for level, path in SOURCES.items()
        ]
    )

    previous16 = ROOT / "outputs/recreated_predictive_models/table16_recreated_baseline_vs_random_forest.csv"
    previous17 = ROOT / "outputs/recreated_predictive_models/table17_recreated_level_ablation_random_forest.csv"
    write_summary(table16, table17, validation, previous16, previous17)

    with pd.ExcelWriter(PRED_DIR / "corrected_predictive_analysis.xlsx") as writer:
        table16.to_excel(writer, sheet_name="table16", index=False)
        table17.to_excel(writer, sheet_name="table17", index=False)
        rounded_metrics.to_excel(writer, sheet_name="all_metrics", index=False)
        pd.concat(all_importances, ignore_index=True).to_excel(writer, sheet_name="feature_importances", index=False)
        pd.DataFrame(feature_count_rows).to_excel(writer, sheet_name="feature_counts", index=False)
        zero_audit.to_excel(writer, sheet_name="zero_rows", index=False)
        pd.DataFrame(missing_rows).to_excel(writer, sheet_name="missing_values", index=False)
        validation.to_excel(writer, sheet_name="sources", index=False)

    digest_input = json.dumps(
        {
            "table16": table16.to_dict(orient="records"),
            "table17": table17.to_dict(orient="records"),
            "config": model_config.to_dict(orient="records"),
        },
        sort_keys=True,
    ).encode("utf-8")
    digest = hashlib.sha256(digest_input).hexdigest()
    elapsed = time.time() - start
    (AUDIT_DIR / "rf_reproducibility_check.txt").write_text(
        "\n".join(
            [
                "Corrected RF reproducibility check",
                f"random_state={RANDOM_STATE}",
                f"n_splits={N_SPLITS}",
                f"n_estimators={N_ESTIMATORS}",
                "n_jobs=1",
                f"metrics_sha256={digest}",
                f"elapsed_seconds={elapsed:.2f}",
                "Rerunning the script with the same corrected inputs and package versions should reproduce the same metric tables.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("\nTable 16 corrected")
    print(table16.to_string(index=False))
    print("\nTable 17 corrected")
    print(table17.to_string(index=False))
    print(f"\nWrote {PRED_DIR.relative_to(ROOT)} and {AUDIT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
