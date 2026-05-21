from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_filtered"
DICT_FILE = BASE_DIR / "outputs" / "dictionary_audit" / "v2_recursive_dictionary_inventory.csv"
OUT_DIR = BASE_DIR / "outputs" / "v2_intersentential_sample"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_N = 1000
RANDOM_SEED = 42

DATASETS = {
    "EFCAMDAT": {
        "file": DATA_DIR / "efcamdat_v2_filtered.csv",
        "id_col": "writing_id",
        "text_col": "text_clean_preserveCase",
        "group_col": "cefr",
    },
    "IELTS": {
        "file": DATA_DIR / "ielts_v2_filtered.csv",
        "id_col": "essay_id",
        "text_col": "text_clean_preserveCase",
        "group_col": "band",
    },
    "GiG": {
        "file": DATA_DIR / "gig_v2_filtered.csv",
        "id_col": "text_id",
        "text_col": "text_clean_preserveCase",
        "group_col": "year_group",
    },
}


def load_intersentential_connectors():
    df = pd.read_csv(DICT_FILE)

    df = df[
        (df["level"] == "inter_sentential")
        & (df["include_main_v2"] == True)
    ].copy()

    df["connector_lower"] = df["connector_lower"].fillna("").str.strip()
    df = df[df["connector_lower"] != ""]

    risky_exact_exclusions = {
        "there",
        "as",
        "for",
        "with",
        "that",
        "this is",
        "here",
    }

    df = df[~df["connector_lower"].isin(risky_exact_exclusions)].copy()

    # Keep longest connector first: "on the other hand" before "on"
    df["connector_len"] = df["connector_lower"].str.split().str.len()
    df = df.sort_values(["connector_len", "connector_lower"], ascending=[False, True])

    return df


def split_sentences(text):
    """
    Conservative lightweight sentence splitter.
    Good enough for V2 sensitivity sample.
    """
    if not isinstance(text, str):
        return []

    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []

    # Split after sentence-final punctuation followed by space + likely new sentence
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'“”‘’A-Z0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def normalise_sentence_start(sentence):
    """
    Remove opening punctuation, numbering, bullets, and quotes before checking marker.
    """
    s = sentence.strip()

    # Remove bullets/numbering like "1.", "a)", "-", "•"
    s = re.sub(r"^[-•\*\s]+", "", s)
    s = re.sub(r"^\(?[0-9]+[\).\:\-]\s*", "", s)
    s = re.sub(r"^[A-Za-z][\).\:\-]\s+", "", s)

    # Remove opening quotes/brackets
    s = re.sub(r"^[\"'“”‘’\(\[\{]+", "", s)

    return s.strip()


def detect_sentence_initial_marker(sentence, connector_df):
    start = normalise_sentence_start(sentence)
    start_lower = start.lower()

    for _, row in connector_df.iterrows():
        connector = row["connector_lower"]

        # Word-boundary-ish match at sentence start
        pattern = r"^" + re.escape(connector) + r"(\b|[,\.;:\?!])"

        if re.search(pattern, start_lower):
            
            # Exclude "in case studies/study" because it is a noun phrase, not a conditional connector.

            if connector == "in case" and re.match(r"^in case stud(y|ies)\b", start_lower):

                continue

            # Exclude fragment-only "so."

            if connector == "so" and re.fullmatch(r"so[\.,;:!\?]?", start_lower.strip()):

                continue
            
            return {
                "detected_item": row["connector"],
                "macro_category": row["path_1"],
                "path_2": row.get("path_2", ""),
                "path_3": row.get("path_3", ""),
                "path_4": row.get("path_4", ""),
                "path_5": row.get("path_5", ""),
                "sentence_start_cleaned": start,
            }

    return None


def process_dataset(corpus, spec, connector_df):
    df = pd.read_csv(spec["file"], low_memory=False)

    sample_n = min(SAMPLE_N, len(df))
    sample = df.sample(n=sample_n, random_state=RANDOM_SEED).copy()

    rows = []

    for _, r in sample.iterrows():
        text_id = r[spec["id_col"]]
        group_value = r[spec["group_col"]]
        text = r[spec["text_col"]]

        sentences = split_sentences(text)

        for i, sent in enumerate(sentences):
            if i == 0:
                # Inter-sentential marker requires a previous sentence.
                continue

            hit = detect_sentence_initial_marker(sent, connector_df)

            if hit:
                rows.append({
                    "corpus": corpus,
                    "text_id": text_id,
                    "group": group_value,
                    "sentence_index": i,
                    "previous_sentence": sentences[i - 1],
                    "current_sentence": sent,
                    **hit,
                    "word_count_text": r.get("wc_preserve", None),
                    "source_file": str(spec["file"]),
                    "algorithm_notes": (
                        "V2 inter-sentential: detects only the first discourse-marker "
                        "sequence at the beginning of the current sentence."
                    ),
                })

    return pd.DataFrame(rows), sample_n


def main():
    connector_df = load_intersentential_connectors()

    all_cases = []
    summary_rows = []

    print("Loaded inter-sentential connectors:", connector_df["connector_lower"].nunique())

    for corpus, spec in DATASETS.items():
        print(f"\nProcessing {corpus}...")
        cases, sample_n = process_dataset(corpus, spec, connector_df)

        all_cases.append(cases)

        summary_rows.append({
            "corpus": corpus,
            "sample_n_texts": sample_n,
            "detected_cases": len(cases),
            "detected_cases_per_text": round(len(cases) / sample_n, 4) if sample_n else 0,
        })

        print("Sample texts:", sample_n)
        print("Detected cases:", len(cases))

    out_cases = pd.concat(all_cases, ignore_index=True) if all_cases else pd.DataFrame()
    out_summary = pd.DataFrame(summary_rows)

    out_cases.to_csv(OUT_DIR / "v2_intersentential_sample_cases.csv", index=False)
    out_summary.to_csv(OUT_DIR / "v2_intersentential_sample_summary.csv", index=False)

    if not out_cases.empty:
        macro_summary = (
            out_cases.groupby(["corpus", "macro_category"])
            .size()
            .reset_index(name="n_cases")
        )
        macro_summary.to_csv(OUT_DIR / "v2_intersentential_sample_macro_summary.csv", index=False)

    print("\nWrote outputs to:", OUT_DIR)
    print("\nSUMMARY")
    print(out_summary.to_string(index=False))


if __name__ == "__main__":
    main()