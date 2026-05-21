from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
IN_DIR = BASE_DIR / "outputs" / "v2_interparagraph_full"
DATA_FILE = BASE_DIR / "data_filtered" / "gig_v2_filtered.csv"

CASES_FILE = IN_DIR / "v2_interparagraph_gig_full_cases.csv"
OUT_FILE = IN_DIR / "v2_interparagraph_gig_full_text_indices.csv"


def main():
    cases = pd.read_csv(CASES_FILE, low_memory=False)

    if "is_interparagraph_supported" not in cases.columns:
        raise ValueError("Missing column: is_interparagraph_supported")

    # Text metadata: one row per eligible GiG text, including zero-marker texts.
    gig = pd.read_csv(DATA_FILE, low_memory=False)
    gig = gig[
        gig["text_clean_preserveCase"].astype(str).str.contains("\n", regex=False, na=False)
    ].copy()
    texts = pd.DataFrame({
        "corpus": "GiG",
        "text_id": gig["text_id"],
        "group": gig["year_group"],
        "word_count_text": gig["wc_preserve"],
        "paragraph_count_text": (
            gig["text_clean_preserveCase"]
            .astype(str)
            .str.strip()
            .str.split(r"\n+", regex=True)
            .apply(lambda x: len([p for p in x if str(p).strip()]))
        ),
    })

    # Broad counts.
    broad_counts = (
        cases.groupby(["corpus", "text_id", "macro_category"])
        .size()
        .reset_index(name="raw_count")
    )

    broad_counts["index_name"] = (
        "interparagraph_"
        + broad_counts["macro_category"].str.lower().str.strip()
    )

    broad_wide = (
        broad_counts.pivot_table(
            index=["corpus", "text_id"],
            columns="index_name",
            values="raw_count",
            fill_value=0,
            aggfunc="sum",
        )
        .reset_index()
    )

    # Supported counts.
    supported = cases[cases["is_interparagraph_supported"] == 1].copy()

    supported_counts = (
        supported.groupby(["corpus", "text_id", "macro_category"])
        .size()
        .reset_index(name="raw_count")
    )

    supported_counts["index_name"] = (
        "supported_interparagraph_"
        + supported_counts["macro_category"].str.lower().str.strip()
    )

    supported_wide = (
        supported_counts.pivot_table(
            index=["corpus", "text_id"],
            columns="index_name",
            values="raw_count",
            fill_value=0,
            aggfunc="sum",
        )
        .reset_index()
    )

    broad_expected = [
        "interparagraph_elaboration",
        "interparagraph_extension",
        "interparagraph_enhancement",
    ]

    supported_expected = [
        "supported_interparagraph_elaboration",
        "supported_interparagraph_extension",
        "supported_interparagraph_enhancement",
    ]

    for col in broad_expected:
        if col not in broad_wide.columns:
            broad_wide[col] = 0

    for col in supported_expected:
        if col not in supported_wide.columns:
            supported_wide[col] = 0

    out = texts.merge(broad_wide, on=["corpus", "text_id"], how="left")
    out = out.merge(supported_wide, on=["corpus", "text_id"], how="left")

    count_cols = broad_expected + supported_expected
    out[count_cols] = out[count_cols].fillna(0).astype(int)

    # Rename raw count columns.
    out = out.rename(columns={col: f"{col}_raw" for col in count_cols})

    broad_raw_cols = [f"{col}_raw" for col in broad_expected]
    supported_raw_cols = [f"{col}_raw" for col in supported_expected]

    out["interparagraph_total_raw"] = out[broad_raw_cols].sum(axis=1)
    out["supported_interparagraph_total_raw"] = out[supported_raw_cols].sum(axis=1)

    out["interparagraph_total_per_1000"] = (
        out["interparagraph_total_raw"] / out["word_count_text"] * 1000
    ).where(out["word_count_text"] > 0)

    out["supported_interparagraph_total_per_1000"] = (
        out["supported_interparagraph_total_raw"] / out["word_count_text"] * 1000
    ).where(out["word_count_text"] > 0)

    for col in broad_raw_cols + supported_raw_cols:
        norm_col = col.replace("_raw", "_per_1000")
        out[norm_col] = (
            out[col] / out["word_count_text"] * 1000
        ).where(out["word_count_text"] > 0)

    out.to_csv(OUT_FILE, index=False)

    print("Wrote:", OUT_FILE)
    print("Rows:", len(out))
    print("Columns:", len(out.columns))

    print("\nBroad vs supported total per 1,000 words:")
    print(
        out.groupby("corpus")
        .agg(
            n_texts=("text_id", "count"),
            mean_broad_per_1000=("interparagraph_total_per_1000", "mean"),
            median_broad_per_1000=("interparagraph_total_per_1000", "median"),
            mean_supported_per_1000=("supported_interparagraph_total_per_1000", "mean"),
            median_supported_per_1000=("supported_interparagraph_total_per_1000", "median"),
        )
        .reset_index()
        .to_string(index=False)
    )

    print("\nMacro means per 1,000 words:")
    norm_cols = [c for c in out.columns if c.endswith("_per_1000")]
    print(
        out.groupby("corpus")[norm_cols]
        .mean()
        .reset_index()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
