#!/usr/bin/env python3
"""Corrected inferential statistics for supported inter-paragraph outputs only."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal, spearmanr


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/v2_interparagraph_full/v2_interparagraph_full_supported_text_indices.csv"
OUT_DIR = ROOT / "outputs/inferential_statistics/interparagraph_corrected"

CORPUS_ORDER = ["COREFL", "GiG"]
CEFR_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

VARIABLES = [
    ("interparagraph_density_per_1000", "Inter-paragraph conjunction density"),
    ("extension_percent", "Extension relations (%)"),
    ("enhancement_percent", "Enhancement relations (%)"),
    ("elaboration_percent", "Elaboration relations (%)"),
]

RAW_COLUMNS = {
    "extension_percent": "supported_interparagraph_extension_raw",
    "enhancement_percent": "supported_interparagraph_enhancement_raw",
    "elaboration_percent": "supported_interparagraph_elaboration_raw",
}
TOTAL = "supported_interparagraph_total_raw"


def epsilon_squared_kruskal(h_stat: float, n: int, k: int) -> float:
    """Kruskal-Wallis epsilon squared, bounded at zero for numerical safety."""
    if n <= k:
        return np.nan
    return max((h_stat - k + 1) / (n - k), 0.0)


def p_label(p_value: float) -> str:
    if pd.isna(p_value):
        return ""
    if p_value < 0.001:
        return "< .001"
    return f"{p_value:.4f}".rstrip("0").rstrip(".")


def effect_label(epsilon: float) -> str:
    if pd.isna(epsilon):
        return ""
    if epsilon >= 0.14:
        return "large"
    if epsilon >= 0.06:
        return "medium"
    if epsilon >= 0.01:
        return "small"
    return "below small"


def prepare_data() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    missing = {
        "corpus",
        "text_id",
        "group",
        "word_count_text",
        TOTAL,
        "supported_interparagraph_total_per_1000",
        *RAW_COLUMNS.values(),
    } - set(df.columns)
    if missing:
        raise ValueError(f"Missing required source columns: {sorted(missing)}")

    unexpected = sorted(set(df["corpus"].dropna()) - set(CORPUS_ORDER))
    if unexpected:
        raise ValueError(f"Unexpected corpora in corrected inter-paragraph file: {unexpected}")

    df = df[df["corpus"].isin(CORPUS_ORDER)].copy()
    df["interparagraph_density_per_1000"] = df["supported_interparagraph_total_per_1000"]

    for variable, raw_col in RAW_COLUMNS.items():
        df[variable] = np.where(df[TOTAL] > 0, df[raw_col] / df[TOTAL] * 100, 0.0)

    category_sum = df[list(RAW_COLUMNS.values())].sum(axis=1)
    if not category_sum.equals(df[TOTAL]):
        mismatch = int((category_sum != df[TOTAL]).sum())
        raise ValueError(f"Category counts do not sum to total in {mismatch} rows")

    df["development_numeric"] = np.nan
    corefl = df["corpus"].eq("COREFL")
    gig = df["corpus"].eq("GiG")
    df.loc[corefl, "development_numeric"] = df.loc[corefl, "group"].map(CEFR_ORDER)
    df.loc[gig, "development_numeric"] = pd.to_numeric(df.loc[gig, "group"], errors="coerce")

    return df


def build_validation(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in CORPUS_ORDER:
        sub = df[df["corpus"].eq(corpus)]
        rows.append(
            {
                "corpus": corpus,
                "eligible_rows": int(len(sub)),
                "zero_density_rows": int(sub[TOTAL].eq(0).sum()),
                "supported_interparagraph_tokens": int(sub[TOTAL].sum()),
                "missing_developmental_metadata": int(sub["development_numeric"].isna().sum()),
                "final_analytic_n": int(sub["development_numeric"].notna().sum()),
                "groups": ", ".join(map(str, sorted(sub["group"].dropna().astype(str).unique()))),
            }
        )
    rows.append(
        {
            "corpus": "TOTAL",
            "eligible_rows": int(len(df)),
            "zero_density_rows": int(df[TOTAL].eq(0).sum()),
            "supported_interparagraph_tokens": int(df[TOTAL].sum()),
            "missing_developmental_metadata": int(df["development_numeric"].isna().sum()),
            "final_analytic_n": int(df["development_numeric"].notna().sum()),
            "groups": "",
        }
    )
    return pd.DataFrame(rows)


def build_descriptives(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in CORPUS_ORDER:
        sub = df[df["corpus"].eq(corpus)]
        for variable, label in VARIABLES:
            rows.append(
                {
                    "corpus": corpus,
                    "variable": variable,
                    "label": label,
                    "n": int(sub[variable].notna().sum()),
                    "mean": sub[variable].mean(),
                    "median": sub[variable].median(),
                    "sd": sub[variable].std(ddof=1),
                    "min": sub[variable].min(),
                    "max": sub[variable].max(),
                }
            )
    return pd.DataFrame(rows)


def build_table14(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    k = len(CORPUS_ORDER)
    for variable, label in VARIABLES:
        samples = [df[df["corpus"].eq(corpus)][variable].dropna() for corpus in CORPUS_ORDER]
        h_stat, p_value = kruskal(*samples)
        n = int(sum(len(sample) for sample in samples))
        epsilon = epsilon_squared_kruskal(float(h_stat), n, k)
        rows.append(
            {
                "variable": label,
                "H": float(h_stat),
                "df": k - 1,
                "p": float(p_value),
                "p_formatted": p_label(float(p_value)),
                "epsilon_squared": epsilon,
                "effect_size_descriptor": effect_label(epsilon),
                "n": n,
                "groups": k,
            }
        )
    return pd.DataFrame(rows)


def build_table15(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in CORPUS_ORDER:
        sub = df[df["corpus"].eq(corpus)].copy()
        for variable, label in VARIABLES:
            analytic = sub[["development_numeric", variable]].dropna()
            rho, p_value = spearmanr(analytic["development_numeric"], analytic[variable])
            rows.append(
                {
                    "corpus": corpus,
                    "variable": label,
                    "rho": float(rho),
                    "p": float(p_value),
                    "p_formatted": p_label(float(p_value)),
                    "n": int(len(analytic)),
                    "missing_developmental_metadata": int(sub["development_numeric"].isna().sum()),
                }
            )
    return pd.DataFrame(rows)


def write_audit(validation: pd.DataFrame) -> None:
    total = validation[validation["corpus"].eq("TOTAL")].iloc[0]
    audit = "\n".join(
        [
            "# Corrected Inter-Paragraph Inferential Statistics Audit",
            "",
            f"Source file: `{SOURCE.relative_to(ROOT)}`",
            "",
            f"Total eligible texts: {int(total['eligible_rows'])}",
            f"Zero-density rows preserved: {int(total['zero_density_rows'])}",
            "EFCAMDAT excluded: yes",
            "Parser rerun: no",
            "Other workflows rerun: no intra-sentential, inter-sentential, or Random Forest workflows were run",
            "Dunn posthoc tests: unnecessary because only two corpora remain; the Kruskal-Wallis test has one corpus contrast.",
            "",
            validation.to_markdown(index=False),
            "",
        ]
    )
    (OUT_DIR / "audit_report.md").write_text(audit, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = prepare_data()
    validation = build_validation(df)
    descriptives = build_descriptives(df)
    table14 = build_table14(df)
    table15 = build_table15(df)

    validation.to_csv(OUT_DIR / "input_validation.csv", index=False)
    descriptives.to_csv(OUT_DIR / "descriptive_summary.csv", index=False)
    table14.to_csv(OUT_DIR / "table14_kruskal_wallis_corrected.csv", index=False)
    table15.to_csv(OUT_DIR / "table15_spearman_correlations_corrected.csv", index=False)

    dunn_note = pd.DataFrame(
        [
            {
                "status": "not_applicable",
                "reason": "Only two corpora remain after excluding EFCAMDAT; Kruskal-Wallis has a single COREFL-GiG contrast, so Dunn posthoc tests are unnecessary.",
            }
        ]
    )
    dunn_note.to_csv(OUT_DIR / "dunn_posthoc_not_applicable.csv", index=False)

    write_audit(validation)

    with pd.ExcelWriter(OUT_DIR / "interparagraph_corrected_inferential_statistics.xlsx") as writer:
        validation.to_excel(writer, sheet_name="validation", index=False)
        descriptives.to_excel(writer, sheet_name="descriptives", index=False)
        table14.to_excel(writer, sheet_name="table14_kw", index=False)
        table15.to_excel(writer, sheet_name="table15_spearman", index=False)
        dunn_note.to_excel(writer, sheet_name="dunn_note", index=False)

    print(f"Wrote {OUT_DIR.relative_to(ROOT)}")
    print(table14.to_string(index=False))
    print()
    print(table15.to_string(index=False))


if __name__ == "__main__":
    main()
