from pathlib import Path
import argparse
import re
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from scripts.run_v2_intrasentential_full import (  # noqa: E402
    detect_intra_markers,
    load_intra_connectors,
    split_sentences,
)


DATA_DIR = BASE_DIR / "data_filtered"
DEFAULT_OUT_DIR = BASE_DIR / "outputs" / "validation" / "medium_batch_rather_check"

DATASETS = {
    "COREFL": DATA_DIR / "corefl_v2_filtered.csv",
    "EFCAMDAT": DATA_DIR / "efcamdat_v2_filtered.csv",
    "GiG": DATA_DIR / "gig_v2_filtered.csv",
    "IELTS": DATA_DIR / "ielts_v2_filtered.csv",
}

LIKELY_TEXT_COLS = ["text", "essay", "clean_text", "raw_text", "response", "writing", "content"]
LIKELY_ID_COLS = ["text_id", "id", "essay_id", "file_id"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a reproducible medium-batch validation check for the supported rather filter."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=200,
        help="Requested number of texts to sample per corpus. Uses all available texts if fewer.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random state used for reproducible sampling.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory for validation CSVs and run summary.",
    )
    return parser.parse_args()


def detect_text_column(df):
    lower_lookup = {col.lower(): col for col in df.columns}
    for name in LIKELY_TEXT_COLS:
        if name in lower_lookup:
            return lower_lookup[name]

    object_cols = [
        col for col in df.columns
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])
    ]
    if not object_cols:
        raise ValueError("Could not detect a text column; no likely or string/object columns found.")

    return max(
        object_cols,
        key=lambda col: df[col].dropna().astype(str).str.len().mean(),
    )


def detect_id_column(df):
    lower_lookup = {col.lower(): col for col in df.columns}
    for name in LIKELY_ID_COLS:
        if name in lower_lookup:
            return lower_lookup[name]
    return None


def detect_group_column(df):
    for col in ["cefr", "year_group", "group", "level"]:
        if col in df.columns:
            return col
    return None


def word_count(text, row):
    if "wc_preserve" in row.index and pd.notna(row["wc_preserve"]):
        return row["wc_preserve"]
    return len(re.findall(r"\b\w+\b", str(text)))


def process_sample(corpus, file_path, connector_df, sample_size, random_state):
    df = pd.read_csv(file_path, low_memory=False)
    text_col = detect_text_column(df)
    id_col = detect_id_column(df)
    group_col = detect_group_column(df)

    sample_n = min(sample_size, len(df))
    sample = df.sample(n=sample_n, random_state=random_state).copy()

    rows = []
    for sample_idx, (_, row) in enumerate(sample.iterrows(), start=1):
        text = row.get(text_col, "")
        text_id = row[id_col] if id_col else f"{corpus}_{sample_idx}"
        group_value = row[group_col] if group_col else ""
        wc = word_count(text, row)
        sentences = split_sentences(text)

        for sentence_index, sentence in enumerate(sentences):
            for hit in detect_intra_markers(sentence, connector_df):
                rows.append({
                    "corpus": corpus,
                    "text_id": text_id,
                    "group": group_value,
                    "sentence_index": sentence_index,
                    **hit,
                    "word_count_text": wc,
                    "sentence_count_text": len(sentences),
                    "source_file": str(file_path),
                })

    return pd.DataFrame(rows), {
        "corpus": corpus,
        "source_file": str(file_path),
        "text_column": text_col,
        "id_column": id_col if id_col else "generated from corpus + sampled row number",
        "requested_sample_size": sample_size,
        "sampled_texts": sample_n,
    }


def write_run_summary(path, sample_info, cases, supported, supported_rather, sample_size, random_state):
    rather_by_corpus = (
        supported_rather.groupby("corpus")
        .size()
        .reset_index(name="supported_rather_cases")
        if not supported_rather.empty
        else pd.DataFrame(columns=["corpus", "supported_rather_cases"])
    )

    lines = []
    lines.append("Medium-batch rather supported-filter check")
    lines.append("")
    lines.append(f"Requested sample size per corpus: {sample_size}")
    lines.append(f"Random state: {random_state}")
    lines.append("")
    lines.append("Actual sample size per corpus:")
    for info in sample_info:
        lines.append(
            f"- {info['corpus']}: {info['sampled_texts']} texts "
            f"(text_col={info['text_column']}; id_col={info['id_column']})"
        )
    lines.append("")
    lines.append(f"Total sampled texts: {sum(info['sampled_texts'] for info in sample_info)}")
    lines.append(f"Total detected cases: {len(cases)}")
    lines.append(f"Total supported cases: {len(supported)}")
    lines.append(f"Total supported rather cases: {len(supported_rather)}")
    lines.append("")
    lines.append("Supported rather cases by corpus:")
    if rather_by_corpus.empty:
        lines.append("(none)")
    else:
        lines.append(rather_by_corpus.to_string(index=False))
    lines.append("")
    lines.append("Expected interpretation:")
    lines.append(
        "bare `rather` should be absent or near absent from supported cases; "
        "valid patterns such as `but rather`, `or rather`, and `rather than` may remain."
    )

    summary = "\n".join(lines)
    path.write_text(summary + "\n", encoding="utf-8")
    print(summary)


def main():
    args = parse_args()
    out_dir = args.output_dir
    if not out_dir.is_absolute():
        out_dir = BASE_DIR / out_dir

    out_dir.mkdir(parents=True, exist_ok=True)
    connector_df = load_intra_connectors()

    case_frames = []
    sample_info = []
    for corpus, file_path in DATASETS.items():
        cases, info = process_sample(
            corpus,
            file_path,
            connector_df,
            sample_size=args.sample_size,
            random_state=args.random_state,
        )
        case_frames.append(cases)
        sample_info.append(info)

    cases = pd.concat(case_frames, ignore_index=True) if case_frames else pd.DataFrame()
    if cases.empty:
        supported = cases.copy()
        supported_rather = cases.copy()
    else:
        supported = cases[cases["is_priming_supported"] == 1].copy()
        supported_rather = supported[
            supported["detected_item"].astype(str).str.lower().str.strip() == "rather"
        ].copy()

    summary_cols = [
        "corpus",
        "detected_item",
        "priming_decision",
        "priming_confidence",
        "is_priming_supported",
        "priming_notes",
    ]
    if supported_rather.empty:
        rather_summary = pd.DataFrame(columns=summary_cols + ["n_cases"])
    else:
        rather_summary = (
            supported_rather.groupby(summary_cols, dropna=False)
            .size()
            .reset_index(name="n_cases")
            .sort_values(["corpus", "n_cases"], ascending=[True, False])
        )

    cases.to_csv(out_dir / "medium_batch_cases.csv", index=False)
    supported.to_csv(out_dir / "medium_batch_supported_cases.csv", index=False)
    supported_rather.to_csv(out_dir / "medium_batch_rather_cases.csv", index=False)
    rather_summary.to_csv(out_dir / "medium_batch_rather_summary.csv", index=False)
    write_run_summary(
        out_dir / "medium_batch_run_summary.txt",
        sample_info,
        cases,
        supported,
        supported_rather,
        sample_size=args.sample_size,
        random_state=args.random_state,
    )

    print("")
    print("Output folder:", out_dir)
    print("Files:")
    for name in [
        "medium_batch_cases.csv",
        "medium_batch_supported_cases.csv",
        "medium_batch_rather_cases.csv",
        "medium_batch_rather_summary.csv",
        "medium_batch_run_summary.txt",
    ]:
        print("-", out_dir / name)


if __name__ == "__main__":
    main()
