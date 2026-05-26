from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    "/private/tmp/conjunction_research_matplotlib_config",
)
os.environ.setdefault(
    "XDG_CACHE_HOME",
    "/private/tmp/conjunction_research_cache",
)

import numpy as np
import pandas as pd
import scikit_posthocs as sp
from scipy import stats


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "v2_intrasentential_full"
    / "v2_intrasentential_full_supported_text_indices.csv"
)
OUT_DIR = BASE_DIR / "outputs" / "inferential_statistics" / "supported_intrasentential"

CORPORA = ["COREFL", "EFCAMDAT", "GiG"]
VARIABLES = [
    ("conjunction_density", "Conjunction density"),
    ("parataxis_density", "Parataxis density"),
    ("hypotaxis_density", "Hypotaxis density"),
    ("extension_density", "Extension density"),
    ("enhancement_density", "Enhancement density"),
    ("elaboration_density", "Elaboration density"),
]

STALE_TABLE9 = {
    "conjunction_density": {"H": 342.57, "p": "< .001", "epsilon_squared": 0.0014},
    "parataxis_density": {"H": 73.04, "p": "< .001", "epsilon_squared": 0.0003},
    "hypotaxis_density": {"H": 2516.89, "p": "< .001", "epsilon_squared": 0.0105},
    "extension_density": {"H": 48.49, "p": "< .001", "epsilon_squared": 0.0002},
    "enhancement_density": {"H": 2346.74, "p": "< .001", "epsilon_squared": 0.0098},
    "elaboration_density": {"H": 1090.91, "p": "< .001", "epsilon_squared": 0.0046},
}

GROUP_ORDINALS = {
    "COREFL": {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6},
    "EFCAMDAT": {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5},
    "GiG": {"2": 2, "4": 4, "6": 6, "9": 9, "11": 11},
}


def p_label(p_value: float) -> str:
    if p_value < 0.001:
        return "< .001"
    return f"{p_value:.4f}"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    df["conjunction_density"] = df["supported_intra_total_per_1000"]
    df["parataxis_density"] = (
        df["supported_intra_paratactic_elaboration_raw"]
        + df["supported_intra_paratactic_extension_raw"]
        + df["supported_intra_paratactic_enhancement_raw"]
    ) / df["word_count_text"] * 1000
    df["hypotaxis_density"] = (
        df["supported_intra_hypotactic_elaboration_raw"]
        + df["supported_intra_hypotactic_extension_raw"]
        + df["supported_intra_hypotactic_enhancement_raw"]
    ) / df["word_count_text"] * 1000
    df["extension_density"] = (
        df["supported_intra_paratactic_extension_raw"]
        + df["supported_intra_hypotactic_extension_raw"]
    ) / df["word_count_text"] * 1000
    df["enhancement_density"] = (
        df["supported_intra_paratactic_enhancement_raw"]
        + df["supported_intra_hypotactic_enhancement_raw"]
    ) / df["word_count_text"] * 1000
    df["elaboration_density"] = (
        df["supported_intra_paratactic_elaboration_raw"]
        + df["supported_intra_hypotactic_elaboration_raw"]
    ) / df["word_count_text"] * 1000

    return df


def validate_input(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in CORPORA:
        corpus_df = df[df["corpus"] == corpus]
        rows.append(
            {
                "corpus": corpus,
                "n_texts": len(corpus_df),
                "zero_density_rows": int(corpus_df["supported_intra_total_raw"].eq(0).sum()),
                "min_word_count": int(corpus_df["word_count_text"].min()),
                "max_word_count": int(corpus_df["word_count_text"].max()),
            }
        )
    return pd.DataFrame(rows)


def descriptive_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in CORPORA:
        corpus_df = df[df["corpus"] == corpus]
        for var, label in VARIABLES:
            rows.append(
                {
                    "corpus": corpus,
                    "variable": var,
                    "label": label,
                    "n": int(corpus_df[var].notna().sum()),
                    "mean": corpus_df[var].mean(),
                    "median": corpus_df[var].median(),
                    "sd": corpus_df[var].std(ddof=1),
                    "zero_rows": int(corpus_df[var].eq(0).sum()),
                }
            )
    return pd.DataFrame(rows)


def kruskal_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n_total = len(df)
    k = len(CORPORA)
    for var, label in VARIABLES:
        groups = [df.loc[df["corpus"] == corpus, var].dropna() for corpus in CORPORA]
        h_stat, p_value = stats.kruskal(*groups)
        epsilon_squared = h_stat / (n_total - 1)
        stale = STALE_TABLE9[var]
        rows.append(
            {
                "variable": var,
                "label": label,
                "H": h_stat,
                "df": k - 1,
                "p": p_value,
                "p_label": p_label(p_value),
                "epsilon_squared": epsilon_squared,
                "n": n_total,
                "stale_H": stale["H"],
                "H_diff": h_stat - stale["H"],
                "stale_epsilon_squared": stale["epsilon_squared"],
                "epsilon_squared_diff": epsilon_squared - stale["epsilon_squared"],
            }
        )
    return pd.DataFrame(rows)


def dunn_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    rows = []
    matrices = {}
    for var, label in VARIABLES:
        matrix = sp.posthoc_dunn(
            df,
            val_col=var,
            group_col="corpus",
            p_adjust="bonferroni",
        )
        matrix = matrix.loc[CORPORA, CORPORA]
        matrices[var] = matrix
        for i, corpus_a in enumerate(CORPORA):
            for corpus_b in CORPORA[i + 1:]:
                p_value = float(matrix.loc[corpus_a, corpus_b])
                rows.append(
                    {
                        "variable": var,
                        "label": label,
                        "comparison": f"{corpus_a} vs {corpus_b}",
                        "group_1": corpus_a,
                        "group_2": corpus_b,
                        "p_bonferroni": p_value,
                        "p_label": p_label(p_value),
                    }
                )
    return pd.DataFrame(rows), matrices


def spearman_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in CORPORA:
        corpus_df = df[df["corpus"] == corpus].copy()
        mapping = GROUP_ORDINALS[corpus]
        corpus_df["group_ordinal"] = corpus_df["group"].astype(str).map(mapping)
        if corpus_df["group_ordinal"].isna().any():
            missing = sorted(corpus_df.loc[corpus_df["group_ordinal"].isna(), "group"].astype(str).unique())
            raise ValueError(f"Missing ordinal mapping for {corpus}: {missing}")

        for var, label in VARIABLES:
            rho, p_value = stats.spearmanr(corpus_df["group_ordinal"], corpus_df[var])
            rows.append(
                {
                    "corpus": corpus,
                    "variable": var,
                    "label": label,
                    "rho": rho,
                    "p": p_value,
                    "p_label": p_label(p_value),
                    "n": int(corpus_df[[var, "group_ordinal"]].dropna().shape[0]),
                    "group_variable": "CEFR" if corpus in {"COREFL", "EFCAMDAT"} else "school_year",
                }
            )
    return pd.DataFrame(rows)


def write_markdown(table9: pd.DataFrame, spearman: pd.DataFrame) -> None:
    table9_md = table9[
        ["label", "H", "df", "p_label", "epsilon_squared", "H_diff", "epsilon_squared_diff"]
    ].copy()
    table9_md["H"] = table9_md["H"].map(lambda x: f"{x:.2f}")
    table9_md["epsilon_squared"] = table9_md["epsilon_squared"].map(lambda x: f"{x:.4f}")
    table9_md["H_diff"] = table9_md["H_diff"].map(lambda x: f"{x:+.2f}")
    table9_md["epsilon_squared_diff"] = table9_md["epsilon_squared_diff"].map(lambda x: f"{x:+.4f}")

    spearman_md = spearman[["corpus", "label", "rho", "p_label", "n"]].copy()
    spearman_md["rho"] = spearman_md["rho"].map(lambda x: f"{x:.3f}")

    out = []
    out.append("# Corrected supported intra-sentential inferential statistics")
    out.append("")
    out.append(f"Primary input: `{INPUT_FILE}`")
    out.append("")
    out.append("## Table 9")
    out.append(table9_md.to_markdown(index=False))
    out.append("")
    out.append("## Spearman correlations")
    out.append(spearman_md.to_markdown(index=False))
    out.append("")
    (OUT_DIR / "supported_intrasentential_inferential_statistics.md").write_text(
        "\n".join(out),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    validation = validate_input(df)
    descriptives = descriptive_summary(df)
    table9 = kruskal_table(df)
    dunn_long, dunn_matrices = dunn_tables(df)
    spearman = spearman_table(df)

    validation.to_csv(OUT_DIR / "input_validation.csv", index=False)
    descriptives.to_csv(OUT_DIR / "descriptive_density_summary.csv", index=False)
    table9.to_csv(OUT_DIR / "table9_kruskal_wallis_corrected.csv", index=False)
    dunn_long.to_csv(OUT_DIR / "dunn_posthoc_bonferroni_corrected.csv", index=False)
    spearman.to_csv(OUT_DIR / "spearman_correlations_corrected.csv", index=False)

    with pd.ExcelWriter(OUT_DIR / "supported_intrasentential_inferential_statistics.xlsx") as writer:
        validation.to_excel(writer, sheet_name="input_validation", index=False)
        descriptives.to_excel(writer, sheet_name="descriptives", index=False)
        table9.to_excel(writer, sheet_name="table9_kruskal", index=False)
        dunn_long.to_excel(writer, sheet_name="dunn_long", index=False)
        spearman.to_excel(writer, sheet_name="spearman", index=False)
        for var, matrix in dunn_matrices.items():
            matrix.to_excel(writer, sheet_name=f"dunn_{var[:20]}")

    write_markdown(table9, spearman)

    print("Input:", INPUT_FILE)
    print("Validation:")
    print(validation.to_string(index=False))
    print("\nTable 9:")
    print(
        table9[
            ["label", "H", "df", "p_label", "epsilon_squared", "H_diff", "epsilon_squared_diff"]
        ].to_string(index=False)
    )
    print("\nSpearman:")
    print(spearman[["corpus", "label", "rho", "p_label", "n"]].to_string(index=False))
    print("\nWrote:", OUT_DIR)


if __name__ == "__main__":
    main()
