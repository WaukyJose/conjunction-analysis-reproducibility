from pathlib import Path
import re
import pandas as pd

from app.output_utils.scalable_indices import (
    add_grouped_path_indices,
    build_item_indices,
)


MODE_PREFIX_BY_ANALYSIS_LEVEL = {
    "intra_sentential_v2": "intra",
    "intra_sentential_supported_v2": "intra",
    "inter_sentential_v2": "intersent",
    "inter_paragraph_v2_true_boundaries": "interpara",
}


def mode_prefix_from_analysis_level(df: pd.DataFrame):
    if "analysis_level" not in df.columns or df["analysis_level"].dropna().empty:
        return None
    analysis_level = str(df["analysis_level"].dropna().iloc[0]).strip()
    return MODE_PREFIX_BY_ANALYSIS_LEVEL.get(analysis_level)


def count_words_from_text_columns(df: pd.DataFrame) -> int:
    """
    Estimate word count from available case-level context columns.

    For single-text app use, this reconstructs text length from unique
    sentence/paragraph strings where possible.
    """
    context_cols = [
        "sentence",
        "current_sentence",
        "previous_sentence",
        "current_paragraph",
        "previous_paragraph",
    ]

    texts = []
    seen = set()

    for col in context_cols:
        if col not in df.columns:
            continue

        for value in df[col].dropna().astype(str):
            value = value.strip()
            if value and value not in seen:
                seen.add(value)
                texts.append(value)

    joined = " ".join(texts)
    return len(re.findall(r"\b\w+\b", joined))


def _build_text_level_index_row(df: pd.DataFrame):
    if "word_count_text" in df.columns and not df["word_count_text"].dropna().empty:
        word_count = int(df["word_count_text"].dropna().iloc[0])
        word_count_source = "parser_full_text"
    else:
        word_count = count_words_from_text_columns(df)
        word_count_source = "estimated_from_detected_context"

    n_cases = len(df)

    row = {
        "text_id": df["text_id"].iloc[0] if "text_id" in df.columns else "",
        "analysis_level": df["analysis_level"].iloc[0] if "analysis_level" in df.columns else "",
        "word_count_text": word_count,
        "word_count_source": word_count_source,
        "detected_cases_raw": n_cases,
        "detected_cases_per_1000": (n_cases / word_count * 1000) if word_count > 0 else 0,
    }

    if "macro_category" in df.columns:
        for macro, count in df["macro_category"].fillna("").astype(str).value_counts().items():
            key = macro.lower().strip().replace(" ", "_").replace("-", "_")
            if key:
                row[f"macro_{key}_raw"] = int(count)
                row[f"macro_{key}_per_1000"] = (count / word_count * 1000) if word_count > 0 else 0

    if "taxis" in df.columns:
        for taxis, count in df["taxis"].fillna("").astype(str).value_counts().items():
            key = taxis.lower().strip().replace(" ", "_").replace("-", "_")
            if key:
                row[f"taxis_{key}_raw"] = int(count)
                row[f"taxis_{key}_per_1000"] = (count / word_count * 1000) if word_count > 0 else 0

    add_grouped_path_indices(row, df, prefix=mode_prefix_from_analysis_level(df))
    return row


def save_text_level_indices(df: pd.DataFrame, output_file, group_by_text=False):
    """
    Save a simple text-level index table beside the case-level output.

    Current scope:
    - one-row summary for the analysed input file
    - raw detected cases
    - estimated per-1,000-word rate
    - macro-category raw and per-1,000 counts
    - taxis raw and per-1,000 counts when available
    """
    output_file = Path(output_file)
    stem = output_file.with_suffix("")
    index_path = Path(f"{stem}_text_indices.csv")

    if df.empty:
        out = pd.DataFrame([{
            "text_id": "",
            "analysis_level": "",
            "word_count_text": 0,
            "word_count_source": "empty_output",
            "detected_cases_raw": 0,
            "detected_cases_per_1000": 0,
        }])
        out.to_csv(index_path, index=False)
        return index_path

    if group_by_text and "text_id" in df.columns:
        rows = [
            _build_text_level_index_row(text_df)
            for _, text_df in df.groupby("text_id", sort=True, dropna=False)
        ]
    else:
        rows = [_build_text_level_index_row(df)]

    out = pd.DataFrame(rows)
    out.to_csv(index_path, index=False)
    return index_path


def _build_item_indices_output(df: pd.DataFrame, group_by_text=False):
    if not group_by_text or df.empty or "text_id" not in df.columns:
        return build_item_indices(df, prefix=mode_prefix_from_analysis_level(df))

    frames = [
        build_item_indices(text_df, prefix=mode_prefix_from_analysis_level(text_df))
        for _, text_df in df.groupby("text_id", sort=True, dropna=False)
    ]
    if not frames:
        return build_item_indices(df, prefix=mode_prefix_from_analysis_level(df))
    return pd.concat(frames, ignore_index=True)


def _save_grouped_summary(df: pd.DataFrame, group_cols, output_path):
    working = df.copy()
    if "detected_item" in group_cols:
        working["detected_item"] = working["detected_item"].str.lower()
    summary = (
        working
        .groupby(group_cols, dropna=False)
        .size()
        .reset_index(name="n_cases")
    )
    summary.to_csv(output_path, index=False)
    return output_path


def save_summary_outputs(df: pd.DataFrame, output_file, group_by_text=False):
    """
    Save TAACO-like summary CSVs beside the main output file.
    """
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    stem = output_file.with_suffix("")

    saved = {
        "item_summary": None,
        "macro_summary": None,
        "taxis_summary": None,
        "text_indices": None,
        "item_indices": None,
    }

    saved["text_indices"] = save_text_level_indices(df, output_file, group_by_text=group_by_text)
    item_indices_path = Path(f"{stem}_item_indices.csv")
    item_indices = _build_item_indices_output(df, group_by_text=group_by_text)
    item_indices.to_csv(item_indices_path, index=False)
    saved["item_indices"] = item_indices_path

    if df.empty:
        if group_by_text:
            empty_summaries = {
                "item_summary": (["text_id", "detected_item", "n_cases"], Path(f"{stem}_summary_by_item.csv")),
                "macro_summary": (["text_id", "macro_category", "n_cases"], Path(f"{stem}_summary_by_macro.csv")),
                "taxis_summary": (["text_id", "taxis", "n_cases"], Path(f"{stem}_summary_by_taxis.csv")),
            }
            for key, (columns, path) in empty_summaries.items():
                pd.DataFrame(columns=columns).to_csv(path, index=False)
                saved[key] = path
        return saved

    if "detected_item" in df.columns:
        item_path = Path(f"{stem}_summary_by_item.csv")
        group_cols = ["detected_item"]
        if group_by_text and "text_id" in df.columns:
            group_cols = ["text_id", *group_cols]
        saved["item_summary"] = _save_grouped_summary(df, group_cols, item_path)

    if "macro_category" in df.columns:
        macro_path = Path(f"{stem}_summary_by_macro.csv")
        group_cols = ["macro_category"]
        if group_by_text and "text_id" in df.columns:
            group_cols = ["text_id", *group_cols]
        saved["macro_summary"] = _save_grouped_summary(df, group_cols, macro_path)

    if "taxis" in df.columns:
        taxis_path = Path(f"{stem}_summary_by_taxis.csv")
        group_cols = ["taxis"]
        if group_by_text and "text_id" in df.columns:
            group_cols = ["text_id", *group_cols]
        saved["taxis_summary"] = _save_grouped_summary(df, group_cols, taxis_path)

    return saved
