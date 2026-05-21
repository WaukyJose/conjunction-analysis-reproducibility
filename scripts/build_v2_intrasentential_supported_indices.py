from pathlib import Path
import pandas as pd

from output_utils.scalable_indices import (
    build_feature_code,
)

BASE_DIR = Path(__file__).resolve().parents[1]
IN_DIR = BASE_DIR / "outputs" / "v2_intrasentential_full"

CASES_FILE = IN_DIR / "v2_intrasentential_full_cases.csv"
TEXT_COUNTS_FILE = IN_DIR / "v2_intrasentential_full_text_counts.csv"

OUT_FILE = IN_DIR / "v2_intrasentential_full_supported_text_indices.csv"
ITEM_OUT_FILE = IN_DIR / "v2_intrasentential_full_supported_item_indices.csv"


def add_feature_codes(df):
    df = df.copy()
    df["feature_code"] = df.apply(
        lambda row: build_feature_code(row, prefix="intra"),
        axis=1,
    )
    return df


def main():
    cases = pd.read_csv(CASES_FILE, low_memory=False)
    texts = pd.read_csv(TEXT_COUNTS_FILE, low_memory=False)

    if "is_priming_supported" not in cases.columns:
        raise ValueError("Missing column: is_priming_supported")

    supported = cases[cases["is_priming_supported"] == 1].copy()
    supported["analysis_level"] = "intra_sentential"

    counts = (
        supported.groupby(["corpus", "text_id", "taxis", "macro_category"])
        .size()
        .reset_index(name="raw_count")
    )

    counts["index_name"] = (
        "supported_intra_"
        + counts["taxis"].str.lower().str.strip()
        + "_"
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
        "supported_intra_paratactic_elaboration",
        "supported_intra_paratactic_extension",
        "supported_intra_paratactic_enhancement",
        "supported_intra_hypotactic_elaboration",
        "supported_intra_hypotactic_extension",
        "supported_intra_hypotactic_enhancement",
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
            "intra_sentential_cases",
            "intra_sentential_per_1000_words",
        ]
    ].merge(wide, on=["corpus", "text_id"], how="left")

    out[expected] = out[expected].fillna(0).astype(int)

    out = out.rename(
        columns={col: f"{col}_raw" for col in expected}
    )

    raw_cols = [f"{col}_raw" for col in expected]

    out["supported_intra_total_raw"] = out[raw_cols].sum(axis=1)
    out["supported_intra_total_per_1000"] = (
        out["supported_intra_total_raw"] / out["word_count_text"] * 1000
    ).where(out["word_count_text"] > 0)

    for col in raw_cols:
        norm_col = col.replace("_raw", "_per_1000")
        out[norm_col] = (
            out[col] / out["word_count_text"] * 1000
        ).where(out["word_count_text"] > 0)

    supported = add_feature_codes(supported)

    grouped_counts = (
        supported.groupby(["corpus", "text_id", "feature_code"])
        .size()
        .reset_index(name="raw_count")
    )
    grouped_counts["raw_col"] = grouped_counts["feature_code"] + "_raw"
    grouped_wide = (
        grouped_counts.pivot_table(
            index=["corpus", "text_id"],
            columns="raw_col",
            values="raw_count",
            fill_value=0,
            aggfunc="sum",
        )
        .reset_index()
    )
    grouped_raw_cols = [
        col for col in grouped_wide.columns
        if col not in {"corpus", "text_id"}
    ]
    out = out.merge(grouped_wide, on=["corpus", "text_id"], how="left")
    out[grouped_raw_cols] = out[grouped_raw_cols].fillna(0).astype(int)
    for raw_col in grouped_raw_cols:
        norm_col = raw_col.replace("_raw", "_per_1000")
        out[norm_col] = (
            out[raw_col] / out["word_count_text"] * 1000
        ).where(out["word_count_text"] > 0)

    item_group_cols = [
        "corpus",
        "text_id",
        "analysis_level",
        "detected_item",
        "feature_code",
        "macro_category",
        "path_2",
        "path_3",
        "path_4",
        "path_5",
        "taxis",
    ]
    item_indices = (
        supported.groupby(item_group_cols, dropna=False)
        .agg(
            raw_count=("detected_item", "size"),
            word_count_text=("word_count_text", "first"),
        )
        .reset_index()
    )
    item_indices["per_1000"] = (
        item_indices["raw_count"] / item_indices["word_count_text"] * 1000
    ).where(item_indices["word_count_text"] > 0, 0)
    item_indices["word_count_source"] = "parser_full_text"
    item_indices = item_indices[
        [
            "text_id",
            "analysis_level",
            "detected_item",
            "feature_code",
            "macro_category",
            "path_2",
            "path_3",
            "path_4",
            "path_5",
            "taxis",
            "raw_count",
            "per_1000",
            "word_count_text",
            "word_count_source",
        ]
    ]

    out.to_csv(OUT_FILE, index=False)
    item_indices.to_csv(ITEM_OUT_FILE, index=False)

    print("Wrote:", OUT_FILE)
    print("Rows:", len(out))
    print("Columns:", len(out.columns))
    print("Wrote:", ITEM_OUT_FILE)
    print("Item rows:", len(item_indices))

    print("\nSupported total per 1,000 words:")
    print(
        out.groupby("corpus")
        .agg(
            n_texts=("text_id", "count"),
            mean_supported_per_1000=("supported_intra_total_per_1000", "mean"),
            median_supported_per_1000=("supported_intra_total_per_1000", "median"),
            mean_broad_per_1000=("intra_sentential_per_1000_words", "mean"),
            median_broad_per_1000=("intra_sentential_per_1000_words", "median"),
        )
        .reset_index()
        .to_string(index=False)
    )

    print("\nSupported macro × taxis means per 1,000:")
    norm_cols = [c for c in out.columns if c.endswith("_per_1000")]
    norm_cols = [c for c in norm_cols if c.startswith("supported_intra_")]
    print(
        out.groupby("corpus")[norm_cols]
        .mean()
        .reset_index()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
