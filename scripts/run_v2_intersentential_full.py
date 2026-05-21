from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_filtered"
DICT_FILE = BASE_DIR / "outputs" / "dictionary_audit" / "v2_recursive_dictionary_inventory.csv"

OUT_DIR = BASE_DIR / "outputs" / "v2_intersentential_full"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "EFCAMDAT": {
        "file": DATA_DIR / "efcamdat_v2_filtered.csv",
        "id_col": "writing_id",
        "text_col": "text_clean_preserveCase",
        "group_col": "cefr",
    },
    
    "COREFL": {
    "file": DATA_DIR / "corefl_v2_filtered.csv",
    "id_col": "text_id",
    "text_col": "text_clean_preserveCase",
    "group_col": "cefr",
    },
    
    "GiG": {
        "file": DATA_DIR / "gig_v2_filtered.csv",
        "id_col": "text_id",
        "text_col": "text_clean_preserveCase",
        "group_col": "year_group",
    },
}


def load_intersent_connectors():
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

    # Longest first: "on the other hand" before "on"
    df["connector_len"] = df["connector_lower"].str.split().str.len()
    df["first_token"] = df["connector_lower"].str.split().str[0]
    df["compiled_pattern"] = df["connector_lower"].apply(
        lambda x: re.compile(r"^" + re.escape(x) + r"(\b|[,\.;:\?!])")
    )
    df = df.sort_values(
        ["first_token", "connector_len", "connector_lower"],
        ascending=[True, False, True],
    )

    return df


def split_sentences(text):
    if not isinstance(text, str):
        return []

    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []

    parts = re.split(r"(?<=[.!?])\s+(?=[\"'“”‘’A-Z0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def normalise_sentence_start(sentence):
    s = sentence.strip()

    # Remove bullets/numbering/opening symbols.
    s = re.sub(r"^[-•\*\s]+", "", s)
    s = re.sub(r"^\(?[0-9]+[\).\:\-]\s*", "", s)
    s = re.sub(r"^[A-Za-z][\).\:\-]\s+", "", s)
    s = re.sub(r"^[\"'“”‘’\(\[\{]+", "", s)

    return s.strip()


def get_intersentential_marker_annotation(connector):
    """
    Marker-confidence annotation for inter-sentential detections.
    Broad output keeps all detections.
    Supported output excludes low-confidence stance/adverbial items.
    """
    connector = str(connector).lower().strip()
    high_confidence = {
        "however", "therefore", "thus", "hence", "consequently",
        "furthermore", "moreover", "in addition", "besides",
        "for example", "for instance", "that is", "in other words",
        "in conclusion", "to conclude", "overall", "on the other hand",
        "nevertheless", "nonetheless", "as a result",
    }
    sequential = {
        "first", "second", "third", "next", "then", "finally",
        "after", "afterwards", "later", "before", "meanwhile",
        "in the end", "at last", "the next day", "in the morning",
        "at the same time", "once",
    }
    conditional_or_frame = {
        "if", "although", "because", "since", "while", "when",
        "even though", "despite", "because of",
    }
    additive_adversative = {
        "and", "but", "also", "yet", "still", "or",
    }
    stance_or_low_confidence = {
        "maybe", "perhaps", "really", "never",
        "fortunately", "unfortunately",
    }
    if connector in high_confidence:
        return {
            "intersentential_marker_type": "high_confidence_discourse_marker",
            "intersentential_confidence": "high",
            "is_intersentential_supported": 1,
            "intersentential_notes": "Core sentence-initial discourse marker.",
        }
    if connector in sequential:
        return {
            "intersentential_marker_type": "sequential_marker",
            "intersentential_confidence": "medium",
            "is_intersentential_supported": 1,
            "intersentential_notes": "Sentence-initial sequencing or temporal organisation marker.",
        }
    if connector in conditional_or_frame:
        return {
            "intersentential_marker_type": "conditional_or_hypotactic_frame",
            "intersentential_confidence": "medium",
            "is_intersentential_supported": 1,
            "intersentential_notes": "Sentence-initial conditional, causal, concessive, or temporal frame.",
        }
    if connector in additive_adversative:
        return {
            "intersentential_marker_type": "additive_or_adversative_marker",
            "intersentential_confidence": "medium",
            "is_intersentential_supported": 1,
            "intersentential_notes": "Sentence-initial additive or adversative marker.",
        }
    if connector in stance_or_low_confidence:
        return {
            "intersentential_marker_type": "stance_or_low_confidence_adverbial",
            "intersentential_confidence": "low",
            "is_intersentential_supported": 0,
            "intersentential_notes": "Sentence-initial stance/adverbial item; excluded from supported inter-sentential subset.",
        }
    return {
        "intersentential_marker_type": "other_dictionary_marker",
        "intersentential_confidence": "medium",
        "is_intersentential_supported": 1,
        "intersentential_notes": "Dictionary-supported sentence-initial marker not in the manually prioritised lists.",
    }


def detect_sentence_initial_marker(sentence, connector_df):
    start = normalise_sentence_start(sentence)
    start_lower = start.lower()
    first_token_match = re.match(r"\w+", start_lower)
    if not first_token_match:
        return None

    first_token = first_token_match.group(0)
    candidate_df = connector_df[connector_df["first_token"] == first_token]

    for _, row in candidate_df.iterrows():
        connector = row["connector_lower"]

        if row["compiled_pattern"].search(start_lower):

            # Exclude "in case studies/study" because it is a noun phrase, not a conditional connector.
            if connector == "in case" and re.match(r"^in case stud(y|ies)\b", start_lower):
                continue

            # Exclude fragment-only "so."
            if connector == "so" and re.fullmatch(r"so[\.,;:!\?]?", start_lower.strip()):
                continue

            hit = {
                "detected_item": row["connector"],
                "macro_category": row["path_1"],
                "path_2": row.get("path_2", ""),
                "path_3": row.get("path_3", ""),
                "path_4": row.get("path_4", ""),
                "path_5": row.get("path_5", ""),
                "sentence_start_cleaned": start,
            }
            hit.update(
                get_intersentential_marker_annotation(row["connector"])
            )
            return hit

    return None


def process_dataset(corpus, spec, connector_df):
    df = pd.read_csv(spec["file"], low_memory=False)

    case_rows = []
    text_rows = []

    total = len(df)

    for idx, r in df.iterrows():
        if (idx + 1) % 1000 == 0 or (idx + 1) == total:
            print(f"{corpus}: processed {idx + 1:,}/{total:,}", flush=True)

        text_id = r[spec["id_col"]]
        group_value = r[spec["group_col"]]
        text = r[spec["text_col"]]
        word_count = r.get("wc_preserve", None)

        sentences = split_sentences(text)
        n_sentences = len(sentences)

        text_case_count = 0

        for i, sent in enumerate(sentences):
            if i == 0:
                continue

            hit = detect_sentence_initial_marker(sent, connector_df)

            if hit:
                text_case_count += 1

                case_rows.append({
                    "corpus": corpus,
                    "text_id": text_id,
                    "group": group_value,
                    "sentence_index": i,
                    "previous_sentence": sentences[i - 1],
                    "current_sentence": sent,
                    **hit,
                    "word_count_text": word_count,
                    "sentence_count_text": n_sentences,
                    "source_file": str(spec["file"]),
                    "algorithm_notes": (
                        "V2 full inter-sentential: detects only the first discourse-marker "
                        "sequence at the beginning of the current sentence. Risky bare markers "
                        "and selected contextual false positives excluded."
                    ),
                })

        text_rows.append({
            "corpus": corpus,
            "text_id": text_id,
            "group": group_value,
            "word_count_text": word_count,
            "sentence_count_text": n_sentences,
            "inter_sentential_cases": text_case_count,
            "inter_sentential_per_100_words": (
                text_case_count / word_count * 100
                if pd.notna(word_count) and word_count > 0 else None
            ),
            "inter_sentential_per_1000_words": (
                text_case_count / word_count * 1000
                if pd.notna(word_count) and word_count > 0 else None
            ),
        })

    return pd.DataFrame(case_rows), pd.DataFrame(text_rows)


def save_summaries(all_cases, all_texts):
    if all_cases.empty:
        return

    all_cases.to_csv(OUT_DIR / "v2_intersentential_full_cases.csv", index=False)
    all_texts.to_csv(OUT_DIR / "v2_intersentential_full_text_counts.csv", index=False)

    corpus_summary = (
        all_texts.groupby("corpus")
        .agg(
            n_texts=("text_id", "count"),
            total_cases=("inter_sentential_cases", "sum"),
            mean_cases_per_text=("inter_sentential_cases", "mean"),
            median_cases_per_text=("inter_sentential_cases", "median"),
            mean_per_1000_words=("inter_sentential_per_1000_words", "mean"),
            median_per_1000_words=("inter_sentential_per_1000_words", "median"),
        )
        .reset_index()
    )
    corpus_summary.to_csv(OUT_DIR / "v2_intersentential_full_corpus_summary.csv", index=False)

    macro_summary = (
        all_cases.groupby(["corpus", "macro_category"])
        .size()
        .reset_index(name="n_cases")
    )
    macro_summary.to_csv(OUT_DIR / "v2_intersentential_full_macro_summary.csv", index=False)

    item_summary = (
        all_cases.groupby(["corpus", "detected_item"])
        .size()
        .reset_index(name="n_cases")
        .sort_values(["corpus", "n_cases"], ascending=[True, False])
    )
    item_summary.to_csv(OUT_DIR / "v2_intersentential_full_item_summary.csv", index=False)

    group_summary = (
        all_texts.groupby(["corpus", "group"])
        .agg(
            n_texts=("text_id", "count"),
            total_cases=("inter_sentential_cases", "sum"),
            mean_cases_per_text=("inter_sentential_cases", "mean"),
            median_cases_per_text=("inter_sentential_cases", "median"),
            mean_per_1000_words=("inter_sentential_per_1000_words", "mean"),
            median_per_1000_words=("inter_sentential_per_1000_words", "median"),
        )
        .reset_index()
    )
    group_summary.to_csv(OUT_DIR / "v2_intersentential_full_group_summary.csv", index=False)


def main():
    connector_df = load_intersent_connectors()

    print("Loaded inter-sentential connectors:", connector_df["connector_lower"].nunique())
    print("Output directory:", OUT_DIR)

    all_case_frames = []
    all_text_frames = []

    for corpus, spec in DATASETS.items():
        print("\n" + "=" * 80)
        print(f"Processing {corpus}")
        print(spec["file"])

        cases, text_counts = process_dataset(corpus, spec, connector_df)

        all_case_frames.append(cases)
        all_text_frames.append(text_counts)

        print(f"{corpus} cases:", len(cases))
        print(f"{corpus} texts:", len(text_counts))

        # Save per-corpus backups as we go.
        cases.to_csv(OUT_DIR / f"v2_intersentential_full_cases_{corpus}.csv", index=False)
        text_counts.to_csv(OUT_DIR / f"v2_intersentential_full_text_counts_{corpus}.csv", index=False)

    all_cases = pd.concat(all_case_frames, ignore_index=True) if all_case_frames else pd.DataFrame()
    all_texts = pd.concat(all_text_frames, ignore_index=True) if all_text_frames else pd.DataFrame()

    save_summaries(all_cases, all_texts)

    print("\n" + "=" * 80)
    print("FULL INTER-SENTENTIAL V2 COMPLETE")
    print("Total cases:", len(all_cases))
    print("Total texts:", len(all_texts))
    print("Outputs saved to:", OUT_DIR)

    if not all_cases.empty:
        print("\nMacro summary:")
        print(
            all_cases.groupby(["corpus", "macro_category"])
            .size()
            .reset_index(name="n_cases")
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
