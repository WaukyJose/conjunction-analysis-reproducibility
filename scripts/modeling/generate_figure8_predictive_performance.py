#!/usr/bin/env python3
"""Generate one Section 4.5 predictive-performance summary figure."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/predictive_analysis_corrected/table17_corrected.csv"
VERIFY = ROOT / "outputs/predictive_analysis_corrected/rf_metrics_all_models.csv"
OUT_DIR = ROOT / "outputs/predictive_analysis_corrected/figures"

PNG = OUT_DIR / "figure8_predictive_performance.png"
PDF = OUT_DIR / "figure8_predictive_performance.pdf"
CAPTION = OUT_DIR / "figure8_caption.txt"
SOURCE_DATA = OUT_DIR / "figure8_source_data.csv"
AUDIT = OUT_DIR / "figure8_audit.md"

FEATURE_LEVELS = [
    "Intra-sentential only",
    "Inter-sentential only",
    "Inter-paragraph only",
    "All available",
]
DISPLAY_LABELS = {
    "Intra-sentential only": "Intra-sentential only",
    "Inter-sentential only": "Inter-sentential only",
    "Inter-paragraph only": "Inter-paragraph only",
    "All available": "Combined features",
}
CORPORA = ["COREFL", "EFCAMDAT", "GiG"]
COLORS = {
    "COREFL": "#4D4D4D",
    "EFCAMDAT": "#9A9A9A",
    "GiG": "#D9D9D9",
}
EDGES = {
    "COREFL": "#222222",
    "EFCAMDAT": "#333333",
    "GiG": "#333333",
}


def load_source() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    required = {"corpus", "feature_level", "rf_macro_f1"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    source_data = df[df["feature_level"].isin(FEATURE_LEVELS) & df["corpus"].isin(CORPORA)].copy()
    source_data = source_data[["corpus", "feature_level", "rf_macro_f1", "rf_macro_f1_sd", "n_texts", "n_features"]]

    duplicate_keys = source_data.duplicated(["corpus", "feature_level"]).sum()
    if duplicate_keys:
        raise ValueError(f"Duplicate corpus/feature-level rows: {duplicate_keys}")

    if ((source_data["corpus"] == "EFCAMDAT") & (source_data["feature_level"] == "Inter-paragraph only")).any():
        raise ValueError("EFCAMDAT inter-paragraph row exists; expected omission.")

    if VERIFY.exists():
        verify = pd.read_csv(VERIFY)
        verify = verify[
            (verify.get("model_family") == "Table 17")
            & verify["feature_scope"].isin(FEATURE_LEVELS)
            & verify["corpus"].isin(CORPORA)
        ].rename(columns={"feature_scope": "feature_level"})
        merged = source_data.merge(
            verify[["corpus", "feature_level", "rf_macro_f1"]],
            on=["corpus", "feature_level"],
            suffixes=("_table17", "_all_metrics"),
            how="left",
        )
        if merged["rf_macro_f1_all_metrics"].isna().any():
            raise ValueError("Optional verification file is missing Table 17 values.")
        max_delta = (merged["rf_macro_f1_table17"] - merged["rf_macro_f1_all_metrics"]).abs().max()
        if max_delta > 1e-12:
            raise ValueError(f"Table 17 and all-metrics values differ by {max_delta}")

    source_data["feature_level"] = pd.Categorical(source_data["feature_level"], FEATURE_LEVELS, ordered=True)
    source_data["corpus"] = pd.Categorical(source_data["corpus"], CORPORA, ordered=True)
    source_data = source_data.sort_values(["feature_level", "corpus"]).reset_index(drop=True)
    source_data["feature_level"] = source_data["feature_level"].astype(str).map(DISPLAY_LABELS)
    return source_data


def plot(source_data: pd.DataFrame) -> None:
    x = np.arange(len(FEATURE_LEVELS))
    width = 0.23
    offsets = {"COREFL": -width, "EFCAMDAT": 0.0, "GiG": width}

    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=150)

    for corpus in CORPORA:
        rows = source_data[source_data["corpus"] == corpus]
        for _, row in rows.iterrows():
            source_level = {display: source for source, display in DISPLAY_LABELS.items()}[str(row["feature_level"])]
            xpos = FEATURE_LEVELS.index(source_level) + offsets[corpus]
            value = float(row["rf_macro_f1"])
            ax.bar(
                xpos,
                value,
                width=width,
                color=COLORS[corpus],
                edgecolor=EDGES[corpus],
                linewidth=0.8,
                label=corpus if str(row["feature_level"]) == FEATURE_LEVELS[0] else None,
            )
            ax.text(
                xpos,
                value + 0.012,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=8,
                rotation=90,
            )

    ax.set_title("Exploratory predictive performance across corpora and feature levels", pad=12)
    ax.set_ylabel("RF macro-F1")
    ax.set_xticks(x)
    ax.set_xticklabels(
        ["Intra-\nsentential", "Inter-\nsentential", "Inter-\nparagraph", "Combined\nfeatures"]
    )
    ax.set_ylim(0, 0.56)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    ax.grid(axis="y", color="#D0D0D0", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(PNG)
    fig.savefig(PDF)
    plt.close(fig)


def write_outputs(source_data: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_data.to_csv(SOURCE_DATA, index=False)
    CAPTION.write_text(
        "Figure 8. Random Forest macro-F1 performance across corpora and feature-level "
        "feature sets, including combined features, using corrected zero-inclusive "
        "position-sensitive conjunction indices.\n",
        encoding="utf-8",
    )

    audit = "\n".join(
        [
            "# Figure 8 Predictive Performance Audit",
            "",
            f"Source file used: `{SOURCE.relative_to(ROOT)}`",
            f"Optional verification file: `{VERIFY.relative_to(ROOT)}`",
            "",
            "- Retraining occurred: no",
            "- Cross-validation rerun: no",
            "- Parser/descriptive/inferential workflows rerun: no",
            "- Values plotted: `rf_macro_f1` only",
            "- EFCAMDAT inter-paragraph bar fabricated: no; omitted because no corrected Table 17 row exists",
            "- Values exactly match corrected Table 17: yes",
            "",
            "## Plotted Values",
            "",
            source_data.to_markdown(index=False, floatfmt=".3f"),
            "",
        ]
    )
    AUDIT.write_text(audit, encoding="utf-8")


def main() -> None:
    source_data = load_source()
    write_outputs(source_data)
    plot(source_data)
    print(f"Wrote {PNG.relative_to(ROOT)}")
    print(f"Wrote {PDF.relative_to(ROOT)}")
    print(f"Wrote {CAPTION.relative_to(ROOT)}")
    print(f"Wrote {SOURCE_DATA.relative_to(ROOT)}")
    print(f"Wrote {AUDIT.relative_to(ROOT)}")
    print(source_data.to_string(index=False))


if __name__ == "__main__":
    main()
