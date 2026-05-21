from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
IN_DIR = BASE_DIR / "outputs" / "v2_intersentential_full"
OUT_FILE = IN_DIR / "v2_intersentential_full_macro_text_indices.csv"

CASES_FILE = IN_DIR / "v2_intersentential_full_cases.csv"
TEXT_COUNTS_FILE = IN_DIR / "v2_intersentential_full_text_counts.csv"


def main():
    cases = pd.read_csv(CASES_FILE, low_memory=False)
    texts = pd.read_csv(TEXT_COUNTS_FILE, low_memory=False)

    macro_counts = (
        cases.groupby(["corpus", "text_id", "macro_category"])
        .size()
        .reset_index(name="raw_count")
    )

    wide = (
        macro_counts.pivot_table(
            index=["corpus", "text_id"],
            columns="macro_category",
            values="raw_count",
            fill_value=0,
            aggfunc="sum",
        )
        .reset_index()
    )

    for col in ["Elaboration", "Extension", "Enhancement"]:
        if col not in wide.columns:
            wide[col] = 0

    wide = wide.rename(columns={
        "Elaboration": "inter_sentential_elaboration_raw",
        "Extension": "inter_sentential_extension_raw",
        "Enhancement": "inter_sentential_enhancement_raw",
    })

    keep_cols = [
        "corpus", "text_id", "group", "word_count_text", "sentence_count_text",
        "inter_sentential_cases",
        "inter_sentential_per_1000_words",
    ]

    out = texts[keep_cols].merge(
        wide,
        on=["corpus", "text_id"],
        how="left"
    )

    raw_cols = [
        "inter_sentential_elaboration_raw",
        "inter_sentential_extension_raw",
        "inter_sentential_enhancement_raw",
    ]

    out[raw_cols] = out[raw_cols].fillna(0).astype(int)

    for raw_col in raw_cols:
        norm_col = raw_col.replace("_raw", "_per_1000")
        out[norm_col] = (
            out[raw_col] / out["word_count_text"] * 1000
        ).where(out["word_count_text"] > 0)

    out.to_csv(OUT_FILE, index=False)

    print("Wrote:", OUT_FILE)
    print("Rows:", len(out))
    print("Columns:", len(out.columns))

    print("\nMean macro indices per 1,000 words:")
    norm_cols = [c for c in out.columns if c.endswith("_per_1000")]
    print(
        out.groupby("corpus")[norm_cols]
        .mean()
        .reset_index()
        .to_string(index=False)
    )

    print("\nMedian macro indices per 1,000 words:")
    print(
        out.groupby("corpus")[norm_cols]
        .median()
        .reset_index()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()