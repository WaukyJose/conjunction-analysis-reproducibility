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

import pandas as pd
import scikit_posthocs as sp
from scipy import stats


BASE_DIR = Path(__file__).resolve().parents[1]
REQUESTED_INPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "v2_intersentential_full"
    / "v2_intersentential_full_text_indices.csv"
)
INPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "v2_intersentential_full"
    / "v2_intersentential_full_supported_text_indices.csv"
)
OUT_DIR = BASE_DIR / "outputs" / "inferential_statistics" / "intersentential_corrected"

CORPORA = ["COREFL", "EFCAMDAT", "GiG"]
VARIABLES = [
    ("inter_sentential_density", "Inter-sentential density"),
    ("inter_sentential_tokens", "Inter-sentential tokens"),
]
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
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    df = pd.read_csv(INPUT_FILE, low_memory=False)
    df["inter_sentential_density"] = df["supported_inter_sentential_total_per_1000"]
    df["inter_sentential_tokens"] = df["supported_inter_sentential_total_raw"]
    return df


def validate_input(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in CORPORA:
        corpus_df = df[df["corpus"] == corpus]
        rows.append(
            {
                "corpus": corpus,
                "n_texts": int(len(corpus_df)),
                "zero_density_rows": int(corpus_df["inter_sentential_tokens"].eq(0).sum()),
                "min_word_count": int(corpus_df["word_count_text"].min()),
                "min_sentence_count": int(corpus_df["sentence_count_text"].min()),
                "zero_sentence_rows": int(corpus_df["sentence_count_text"].eq(0).sum()),
                "source_file": str(INPUT_FILE),
                "requested_file_exists": REQUESTED_INPUT_FILE.exists(),
                "requested_file": str(REQUESTED_INPUT_FILE),
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
    for var, label in VARIABLES:
        groups = [df.loc[df["corpus"] == corpus, var].dropna() for corpus in CORPORA]
        h_stat, p_value = stats.kruskal(*groups)
        rows.append(
            {
                "variable": var,
                "label": label,
                "H": h_stat,
                "df": len(CORPORA) - 1,
                "p": p_value,
                "p_label": p_label(p_value),
                "epsilon_squared": h_stat / (n_total - 1),
                "n": n_total,
            }
        )
    return pd.DataFrame(rows)


def dunn_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for var, label in VARIABLES:
        matrix = sp.posthoc_dunn(
            df,
            val_col=var,
            group_col="corpus",
            p_adjust="bonferroni",
        ).loc[CORPORA, CORPORA]
        matrix.to_csv(OUT_DIR / f"dunn_matrix_{var}_bonferroni.csv")
        for i, group_1 in enumerate(CORPORA):
            for group_2 in CORPORA[i + 1:]:
                p_value = float(matrix.loc[group_1, group_2])
                rows.append(
                    {
                        "variable": var,
                        "label": label,
                        "comparison": f"{group_1} vs {group_2}",
                        "group_1": group_1,
                        "group_2": group_2,
                        "p_bonferroni": p_value,
                        "p_label": p_label(p_value),
                    }
                )
    return pd.DataFrame(rows)


def spearman_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in CORPORA:
        corpus_df = df[df["corpus"] == corpus].copy()
        corpus_df["group_ordinal"] = corpus_df["group"].astype(str).map(
            GROUP_ORDINALS[corpus]
        )
        if corpus_df["group_ordinal"].isna().any():
            missing = sorted(
                corpus_df.loc[corpus_df["group_ordinal"].isna(), "group"]
                .astype(str)
                .unique()
            )
            raise ValueError(f"Missing ordinal mapping for {corpus}: {missing}")

        rho, p_value = stats.spearmanr(
            corpus_df["group_ordinal"],
            corpus_df["inter_sentential_density"],
        )
        rows.append(
            {
                "corpus": corpus,
                "variable": "inter_sentential_density",
                "label": "Inter-sentential density",
                "rho": rho,
                "p": p_value,
                "p_label": p_label(p_value),
                "n": int(corpus_df[["group_ordinal", "inter_sentential_density"]].dropna().shape[0]),
                "group_variable": "CEFR" if corpus in {"COREFL", "EFCAMDAT"} else "school_year",
            }
        )
    return pd.DataFrame(rows)


def write_markdown(
    validation: pd.DataFrame,
    kruskal: pd.DataFrame,
    dunn: pd.DataFrame,
    spearman: pd.DataFrame,
) -> None:
    kruskal_md = kruskal[["label", "H", "df", "p_label", "epsilon_squared", "n"]].copy()
    kruskal_md["H"] = kruskal_md["H"].map(lambda x: f"{x:.2f}")
    kruskal_md["epsilon_squared"] = kruskal_md["epsilon_squared"].map(lambda x: f"{x:.4f}")

    spearman_md = spearman[["corpus", "label", "rho", "p_label", "n"]].copy()
    spearman_md["rho"] = spearman_md["rho"].map(lambda x: f"{x:.3f}")

    out = [
        "# Corrected inter-sentential inferential statistics",
        "",
        f"Requested source: `{REQUESTED_INPUT_FILE}`",
        f"Actual corrected supported source used: `{INPUT_FILE}`",
        "",
        "## Input validation",
        validation.to_markdown(index=False),
        "",
        "## Kruskal-Wallis",
        kruskal_md.to_markdown(index=False),
        "",
        "## Dunn posthoc, Bonferroni",
        dunn.to_markdown(index=False),
        "",
        "## Spearman correlations",
        spearman_md.to_markdown(index=False),
        "",
    ]
    (OUT_DIR / "intersentential_corrected_inferential_statistics.md").write_text(
        "\n".join(out),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    validation = validate_input(df)
    descriptives = descriptive_summary(df)
    kruskal = kruskal_table(df)
    dunn = dunn_table(df)
    spearman = spearman_table(df)

    validation.to_csv(OUT_DIR / "input_validation.csv", index=False)
    descriptives.to_csv(OUT_DIR / "descriptive_summary.csv", index=False)
    kruskal.to_csv(OUT_DIR / "kruskal_wallis_corrected.csv", index=False)
    dunn.to_csv(OUT_DIR / "dunn_posthoc_bonferroni_corrected.csv", index=False)
    spearman.to_csv(OUT_DIR / "spearman_density_corrected.csv", index=False)

    with pd.ExcelWriter(OUT_DIR / "intersentential_corrected_inferential_statistics.xlsx") as writer:
        validation.to_excel(writer, sheet_name="input_validation", index=False)
        descriptives.to_excel(writer, sheet_name="descriptives", index=False)
        kruskal.to_excel(writer, sheet_name="kruskal", index=False)
        dunn.to_excel(writer, sheet_name="dunn_bonferroni", index=False)
        spearman.to_excel(writer, sheet_name="spearman_density", index=False)

    write_markdown(validation, kruskal, dunn, spearman)

    print("Requested input:", REQUESTED_INPUT_FILE)
    print("Requested input exists:", REQUESTED_INPUT_FILE.exists())
    print("Actual input:", INPUT_FILE)
    print("\nValidation:")
    print(validation.to_string(index=False))
    print("\nKruskal-Wallis:")
    print(kruskal[["label", "H", "df", "p_label", "epsilon_squared", "n"]].to_string(index=False))
    print("\nDunn posthoc:")
    print(dunn.to_string(index=False))
    print("\nSpearman:")
    print(spearman[["corpus", "label", "rho", "p_label", "n"]].to_string(index=False))
    print("\nWrote:", OUT_DIR)


if __name__ == "__main__":
    main()
