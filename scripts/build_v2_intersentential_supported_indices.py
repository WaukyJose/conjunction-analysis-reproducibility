from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
IN_DIR = BASE_DIR / "outputs" / "v2_intersentential_full"

CASES_FILE = IN_DIR / "v2_intersentential_full_cases.csv"
TEXT_COUNTS_FILE = IN_DIR / "v2_intersentential_full_text_counts.csv"

OUT_FILE = IN_DIR / "v2_intersentential_full_supported_text_indices.csv"


def main():
    cases = pd.read_csv(CASES_FILE, low_memory=False)
    texts = pd.read_csv(TEXT_COUNTS_FILE, low_memory=False)

    if "is_intersentential_supported" not in cases.columns:
        raise ValueError("Missing column: is_intersentential_supported")

    supported = cases[cases["is_intersentential_supported"] == 1].copy()

    counts = (
        supported.groupby(["corpus", "text_id", "macro_category"])
        .size()
        .reset_index(name="raw_count")
    )

    counts["index_name"] = (
        "supported_inter_sentential_"
        + counts["macro_category"].str.lower().str.strip()
    )

    wide = (
        counts.pivot_table(
            index=["corpus", "text_id"],
            columns="index_name",
            values="raw_count",
            fill_value=0,
            aggfunc="sum",
        )
        .reset_index()
    )

    expected = [
        "supported_inter_sentential_elaboration",
        "supported_inter_sentential_extension",
        "supported_inter_sentential_enhancement",
    ]

    for col in expected:
        if col not in wide.columns:
            wide[col] = 0

    out = texts[
        [
            "corpus",
            "text_id",
            "group",
            "word_count_text",
            "sentence_count_text",
            "inter_sentential_cases",
            "inter_sentential_per_1000_words",
        ]
    ].merge(wide, on=["corpus", "text_id"], how="left")

    out[expected] = out[expected].fillna(0).astype(int)

    out = out.rename(columns={col: f"{col}_raw" for col in expected})

    raw_cols = [f"{col}_raw" for col in expected]

    out["supported_inter_sentential_total_raw"] = out[raw_cols].sum(axis=1)
    out["supported_inter_sentential_total_per_1000"] = (
        out["supported_inter_sentential_total_raw"] / out["word_count_text"] * 1000
    ).where(out["word_count_text"] > 0)

    for col in raw_cols:
        norm_col = col.replace("_raw", "_per_1000")
        out[norm_col] = (
            out[col] / out["word_count_text"] * 1000
        ).where(out["word_count_text"] > 0)

    out.to_csv(OUT_FILE, index=False)

    print("Wrote:", OUT_FILE)
    print("Rows:", len(out))
    print("Columns:", len(out.columns))

    print("\nSupported total per 1,000 words:")
    print(
        out.groupby("corpus")
        .agg(
            n_texts=("text_id", "count"),
            mean_supported_per_1000=("supported_inter_sentential_total_per_1000", "mean"),
            median_supported_per_1000=("supported_inter_sentential_total_per_1000", "median"),
            mean_broad_per_1000=("inter_sentential_per_1000_words", "mean"),
            median_broad_per_1000=("inter_sentential_per_1000_words", "median"),
        )
        .reset_index()
        .to_string(index=False)
    )

    print("\nSupported macro means per 1,000:")
    norm_cols = [
        c for c in out.columns
        if c.startswith("supported_inter_sentential_") and c.endswith("_per_1000")
    ]
    print(
        out.groupby("corpus")[norm_cols]
        .mean()
        .reset_index()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()