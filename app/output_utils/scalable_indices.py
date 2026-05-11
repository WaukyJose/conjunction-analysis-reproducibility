import re

import pandas as pd


ABBREVIATION_MAP = {
    "Enhancement": "enh",
    "Extension": "ext",
    "Elaboration": "elab",
    "Temporal": "temp",
    "Causal-Conditional": "caus",
    "Spatial": "spat",
    "Manner": "manner",
    "Matter": "matter",
    "Addition": "add",
    "Variation": "var",
    "Adversative": "adv",
    "Apposition": "app",
    "Clarifying": "clar",
    "Amplification": "amp",
    "Simultaneous": "sim",
    "Later": "later",
    "Earlier": "earlier",
    "Conclusive": "concl",
    "Reason": "reason",
    "Result": "result",
    "Purpose": "purpose",
    "Conditional": "cond",
    "Concessive": "conc",
    "Replacive": "repl",
    "Subtractive": "subtr",
    "Alternative": "alt",
    "Exemplifying": "exemp",
    "Summative": "sum",
    "Verificative": "verif",
    "paratactic": "para",
    "hypotactic": "hypo",
}

ITEM_INDEX_COLUMNS = [
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


def normalise_label(label):
    value = str(label).lower().strip()
    value = re.sub(r"[\s-]+", "_", value)
    value = re.sub(r"[^a-z0-9_]", "", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def abbreviate_label(label):
    return ABBREVIATION_MAP.get(str(label), normalise_label(label))


def _is_empty(value):
    return (
        value is None
        or pd.isna(value)
        or str(value).strip() == ""
        or str(value).lower() == "nan"
    )


def build_feature_code(row, prefix=None):
    parts = []
    if prefix:
        parts.append(prefix)

    path_values = []
    for field in ["macro_category", "path_2", "path_3", "path_4", "path_5"]:
        value = row.get(field)
        if not _is_empty(value):
            path_values.append(value)

    taxis = row.get("taxis")
    path_normalised = {normalise_label(value) for value in path_values}

    for value in path_values:
        parts.append(abbreviate_label(value))

    if not _is_empty(taxis) and normalise_label(taxis) not in path_normalised:
        parts.append(abbreviate_label(taxis))

    return "_".join(parts)


def _first_value(df, column):
    if column not in df.columns:
        return None
    values = df[column].dropna()
    if values.empty:
        return None
    return values.iloc[0]


def build_item_indices(df, prefix=None):
    if df.empty or "detected_item" not in df.columns:
        return pd.DataFrame(columns=ITEM_INDEX_COLUMNS)

    working = df.copy()
    group_cols = [
        "detected_item",
        "macro_category",
        "path_2",
        "path_3",
        "path_4",
        "path_5",
        "taxis",
    ]

    for col in group_cols:
        if col not in working.columns:
            working[col] = pd.NA

    text_id = _first_value(working, "text_id")
    analysis_level = _first_value(working, "analysis_level")

    if "word_count_text" in working.columns:
        word_count = _first_value(working, "word_count_text")
        word_count = 0 if _is_empty(word_count) else word_count
        word_count_source = "parser_full_text"
    else:
        word_count = 0
        word_count_source = "missing"

    rows = []
    grouped = (
        working.groupby(group_cols, dropna=False)
        .size()
        .reset_index(name="raw_count")
    )

    for row in grouped.to_dict(orient="records"):
        raw_count = int(row["raw_count"])
        numeric_word_count = pd.to_numeric(pd.Series([word_count]), errors="coerce").iloc[0]
        per_1000 = (
            raw_count / numeric_word_count * 1000
            if pd.notna(numeric_word_count) and numeric_word_count > 0
            else 0
        )
        rows.append({
            "text_id": text_id,
            "analysis_level": analysis_level,
            "detected_item": row["detected_item"],
            "feature_code": build_feature_code(row, prefix=prefix),
            "macro_category": row["macro_category"],
            "path_2": row["path_2"],
            "path_3": row["path_3"],
            "path_4": row["path_4"],
            "path_5": row["path_5"],
            "taxis": row["taxis"],
            "raw_count": raw_count,
            "per_1000": per_1000,
            "word_count_text": numeric_word_count if pd.notna(numeric_word_count) else 0,
            "word_count_source": word_count_source,
        })

    return pd.DataFrame(rows, columns=ITEM_INDEX_COLUMNS)


def add_grouped_path_indices(row_dict, df, prefix=None):
    if df.empty:
        return row_dict

    working = df.copy()
    path_cols = ["macro_category", "path_2", "path_3", "path_4", "path_5", "taxis"]

    for col in path_cols:
        if col not in working.columns:
            working[col] = pd.NA

    if "word_count_text" in working.columns:
        word_count = _first_value(working, "word_count_text")
        word_count = 0 if _is_empty(word_count) else word_count
    else:
        word_count = 0

    numeric_word_count = pd.to_numeric(pd.Series([word_count]), errors="coerce").iloc[0]

    working["feature_code"] = working.apply(
        lambda row: build_feature_code(row, prefix=prefix),
        axis=1,
    )
    grouped = working.groupby("feature_code").size().reset_index(name="raw_count")

    for row in grouped.itertuples(index=False):
        raw_count = int(row.raw_count)
        per_1000 = (
            raw_count / numeric_word_count * 1000
            if pd.notna(numeric_word_count) and numeric_word_count > 0
            else 0
        )
        row_dict[f"{row.feature_code}_raw"] = raw_count
        row_dict[f"{row.feature_code}_per_1000"] = float(per_1000)

    return row_dict


if __name__ == "__main__":
    test_row = {
        "macro_category": "Enhancement",
        "path_2": "Causal-Conditional",
        "path_3": "Reason",
        "taxis": "hypotactic",
    }
    print(build_feature_code(test_row, prefix="intra"))

    test_df = pd.DataFrame([
        {
            "text_id": "T001",
            "analysis_level": "intra_sentential",
            "detected_item": "because",
            "macro_category": "Enhancement",
            "path_2": "Causal-Conditional",
            "path_3": "Reason",
            "taxis": "hypotactic",
            "word_count_text": 36,
        },
        {
            "text_id": "T001",
            "analysis_level": "intra_sentential",
            "detected_item": "but",
            "macro_category": "Enhancement",
            "path_2": "Causal-Conditional",
            "path_3": "Concessive",
            "taxis": "paratactic",
            "word_count_text": 36,
        },
    ])
    print(build_item_indices(test_df, prefix="intra"))

    row_dict = {}
    add_grouped_path_indices(row_dict, test_df, prefix="intra")
    print(row_dict)
