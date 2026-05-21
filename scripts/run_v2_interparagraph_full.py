from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_filtered"
DICT_FILE = BASE_DIR / "outputs" / "dictionary_audit" / "v2_recursive_dictionary_inventory.csv"
OUT_DIR = BASE_DIR / "outputs" / "v2_interparagraph_full"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "COREFL": {
        "file": DATA_DIR / "corefl_v2_filtered_50.csv",
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


def load_interparagraph_connectors():
    df = pd.read_csv(DICT_FILE)

    df = df[
        (df["level"] == "inter_paragraph")
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
        "should",
        "consider",
        "results",
    }

    df = df[~df["connector_lower"].isin(risky_exact_exclusions)].copy()

    # Longest first within same first-token group:
    # "on the other hand" before shorter "on..." candidates.
    df["connector_len"] = df["connector_lower"].str.split().str.len()
    df["first_token"] = df["connector_lower"].str.split().str[0]
    df = df.sort_values(
        ["first_token", "connector_len", "connector_lower"],
        ascending=[True, False, True],
    )
    df["compiled_pattern"] = df["connector_lower"].apply(
        lambda x: re.compile(r"^" + re.escape(x) + r"(\b|[,\.;:\?!])")
    )

    return df


def split_paragraphs(text):
    """
    True paragraph splitter based on newline boundaries.
    Single newlines are accepted because GiG often preserves paragraphing that way.
    """
    if not isinstance(text, str):
        return []

    text = text.strip()
    if not text:
        return []

    parts = re.split(r"\n+", text)
    parts = [re.sub(r"\s+", " ", p.strip()) for p in parts]
    return [p for p in parts if p]


def paragraph_has_real_boundary(text):
    return isinstance(text, str) and "\n" in text.strip()


def safe_rate(raw, denominator, multiplier=1):
    if pd.isna(denominator) or denominator <= 0:
        return 0
    return raw / denominator * multiplier


def normalise_paragraph_start(paragraph):
    p = paragraph.strip()

    # Remove bullets/numbering like "1.", "a)", "-", "•"
    p = re.sub(r"^[-•\*\s]+", "", p)
    p = re.sub(r"^\(?[0-9]+[\).\:\-]\s*", "", p)
    p = re.sub(r"^[A-Za-z][\).\:\-]\s+", "", p)

    # Remove opening quotes/brackets
    p = re.sub(r"^[\"'“”‘’\(\[\{]+", "", p)

    return p.strip()


def get_interparagraph_marker_annotation(connector):
    """
    Marker-confidence annotation for inter-paragraph detections.

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
            "interparagraph_marker_type": "high_confidence_discourse_marker",
            "interparagraph_confidence": "high",
            "is_interparagraph_supported": 1,
            "interparagraph_notes": "Core paragraph-initial discourse marker.",
        }

    if connector in sequential:
        return {
            "interparagraph_marker_type": "sequential_marker",
            "interparagraph_confidence": "medium",
            "is_interparagraph_supported": 1,
            "interparagraph_notes": "Paragraph-initial sequencing or temporal organisation marker.",
        }

    if connector in conditional_or_frame:
        return {
            "interparagraph_marker_type": "conditional_or_hypotactic_frame",
            "interparagraph_confidence": "medium",
            "is_interparagraph_supported": 1,
            "interparagraph_notes": "Paragraph-initial conditional, causal, concessive, or temporal frame.",
        }

    if connector in additive_adversative:
        return {
            "interparagraph_marker_type": "additive_or_adversative_marker",
            "interparagraph_confidence": "medium",
            "is_interparagraph_supported": 1,
            "interparagraph_notes": "Paragraph-initial additive or adversative marker.",
        }

    if connector in stance_or_low_confidence:
        return {
            "interparagraph_marker_type": "stance_or_low_confidence_adverbial",
            "interparagraph_confidence": "low",
            "is_interparagraph_supported": 0,
            "interparagraph_notes": "Paragraph-initial stance/adverbial item; excluded from supported inter-paragraph subset.",
        }

    return {
        "interparagraph_marker_type": "other_dictionary_marker",
        "interparagraph_confidence": "medium",
        "is_interparagraph_supported": 1,
        "interparagraph_notes": "Dictionary-supported paragraph-initial marker not in the manually prioritised lists.",
    }


def detect_paragraph_initial_marker(paragraph, connector_df):
    start = normalise_paragraph_start(paragraph)
    start_lower = start.lower()
    if not start_lower:
        return None

    first_match = re.match(r"^[a-z]+(?:\.[a-z]+\.)?", start_lower)
    if not first_match:
        return None

    first_token = first_match.group(0)
    candidates = connector_df[connector_df["first_token"] == first_token]
    if candidates.empty:
        return None

    for _, row in candidates.iterrows():
        connector = row["connector_lower"]

        if row["compiled_pattern"].search(start_lower):
            # Exclude "in case studies/study"
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
                "paragraph_start_cleaned": start,
            }
            hit.update(
                get_interparagraph_marker_annotation(row["connector"])
            )
            return hit

    return None


def build_text_counts(corpus, eligible_df, cases, spec):
    text_counts = pd.DataFrame({
        "corpus": corpus,
        "text_id": eligible_df[spec["id_col"]],
        "group": eligible_df[spec["group_col"]],
        "word_count_text": eligible_df["wc_preserve"],
        "paragraph_count_text": eligible_df["paragraph_count_text"],
    })
    text_counts["eligible_paragraph_starts"] = (
        text_counts["paragraph_count_text"].fillna(0).astype(int) - 1
    ).clip(lower=0)

    macro_names = ["elaboration", "enhancement", "extension"]
    for macro in macro_names:
        text_counts[f"interparagraph_{macro}_raw"] = 0
        text_counts[f"supported_interparagraph_{macro}_raw"] = 0

    if not cases.empty:
        broad_counts = (
            cases.groupby(["text_id", "macro_category"])
            .size()
            .reset_index(name="raw_count")
        )
        supported_counts = (
            cases[cases["is_interparagraph_supported"] == 1]
            .groupby(["text_id", "macro_category"])
            .size()
            .reset_index(name="raw_count")
        )

        for macro in ["Elaboration", "Enhancement", "Extension"]:
            macro_slug = macro.lower()
            broad_map = broad_counts[broad_counts["macro_category"] == macro].set_index("text_id")["raw_count"]
            supported_map = supported_counts[supported_counts["macro_category"] == macro].set_index("text_id")["raw_count"]
            text_counts[f"interparagraph_{macro_slug}_raw"] = (
                text_counts["text_id"].map(broad_map).fillna(0).astype(int)
            )
            text_counts[f"supported_interparagraph_{macro_slug}_raw"] = (
                text_counts["text_id"].map(supported_map).fillna(0).astype(int)
            )

    broad_raw_cols = [f"interparagraph_{macro}_raw" for macro in macro_names]
    supported_raw_cols = [f"supported_interparagraph_{macro}_raw" for macro in macro_names]
    text_counts["interparagraph_total_raw"] = text_counts[broad_raw_cols].sum(axis=1)
    text_counts["supported_interparagraph_total_raw"] = text_counts[supported_raw_cols].sum(axis=1)

    rate_bases = (
        ["interparagraph_total", "supported_interparagraph_total"]
        + [f"interparagraph_{macro}" for macro in macro_names]
        + [f"supported_interparagraph_{macro}" for macro in macro_names]
    )
    for base in rate_bases:
        raw_col = f"{base}_raw"
        text_counts[f"{base}_per_1000"] = text_counts.apply(
            lambda row: safe_rate(row[raw_col], row["word_count_text"], 1000),
            axis=1,
        )
        text_counts[f"{base}_per_eligible_paragraph_start"] = text_counts.apply(
            lambda row: safe_rate(row[raw_col], row["eligible_paragraph_starts"]),
            axis=1,
        )

    return text_counts


def process_dataset(corpus, spec, connector_df):
    df = pd.read_csv(spec["file"], low_memory=False)

    # Only texts with explicit newline paragraph boundaries.
    df["has_real_paragraph_boundary"] = df[spec["text_col"]].apply(paragraph_has_real_boundary)
    eligible_df = df[df["has_real_paragraph_boundary"]].copy()
    eligible_df["paragraph_count_text"] = eligible_df[spec["text_col"]].apply(
        lambda text: len(split_paragraphs(text))
    )

    total = len(eligible_df)

    rows = []

    for idx, (_, r) in enumerate(eligible_df.iterrows()):
        if (idx + 1) % 1000 == 0 or (idx + 1) == total:
            print(f"{corpus}: processed {idx + 1:,}/{total:,}", flush=True)

        text_id = r[spec["id_col"]]
        group_value = r[spec["group_col"]]
        text = r[spec["text_col"]]

        paragraphs = split_paragraphs(text)

        for i, paragraph in enumerate(paragraphs):
            if i == 0:
                # Inter-paragraph marker requires a previous paragraph.
                continue

            hit = detect_paragraph_initial_marker(paragraph, connector_df)

            if hit:
                rows.append({
                    "corpus": corpus,
                    "text_id": text_id,
                    "group": group_value,
                    "paragraph_index": i,
                    "previous_paragraph": paragraphs[i - 1],
                    "current_paragraph": paragraph,
                    **hit,
                    "word_count_text": r.get("wc_preserve", None),
                    "paragraph_count_text": len(paragraphs),
                    "source_file": str(spec["file"]),
                    "algorithm_notes": (
                        "V2 inter-paragraph: COREFL and GiG only; EFCAMDAT excluded because "
                        "paragraph boundaries are not preserved. Detects first discourse-marker "
                        "sequence at the beginning of paragraphs with explicit newline boundaries. "
                        "Stance_Markers excluded from main analysis."
                    ),
                })

    case_columns = [
        "corpus", "text_id", "group", "paragraph_index", "previous_paragraph",
        "current_paragraph", "detected_item", "macro_category", "path_2", "path_3",
        "path_4", "path_5", "paragraph_start_cleaned", "interparagraph_marker_type",
        "interparagraph_confidence", "is_interparagraph_supported", "interparagraph_notes",
        "word_count_text", "paragraph_count_text", "source_file", "algorithm_notes",
    ]
    cases = pd.DataFrame(rows, columns=case_columns)
    text_counts = build_text_counts(corpus, eligible_df, cases, spec)
    summary = {
        "corpus": corpus,
        "total_texts": len(df),
        "eligible_texts_with_newline_boundaries": len(eligible_df),
        "detected_cases": len(cases),
        "detected_cases_per_eligible_text": (
            round(len(cases) / len(eligible_df), 4) if len(eligible_df) else 0
        ),
    }

    return cases, text_counts, summary


def main():
    connector_df = load_interparagraph_connectors()

    print("Loaded inter-paragraph connectors:", connector_df["connector_lower"].nunique())

    case_frames = []
    text_count_frames = []
    summary_rows = []

    for corpus, spec in DATASETS.items():
        cases, text_counts, summary = process_dataset(corpus, spec, connector_df)
        case_frames.append(cases)
        text_count_frames.append(text_counts)
        summary_rows.append(summary)

        cases.to_csv(OUT_DIR / f"v2_interparagraph_full_cases_{corpus}.csv", index=False)
        text_counts.to_csv(
            OUT_DIR / f"v2_interparagraph_full_text_counts_{corpus}.csv",
            index=False,
        )

    combined_cases = pd.concat(case_frames, ignore_index=True)
    combined_text_counts = pd.concat(text_count_frames, ignore_index=True)
    summary = pd.DataFrame(summary_rows)

    combined_cases.to_csv(OUT_DIR / "v2_interparagraph_full_cases.csv", index=False)
    combined_text_counts.to_csv(OUT_DIR / "v2_interparagraph_full_text_counts.csv", index=False)
    summary.to_csv(OUT_DIR / "v2_interparagraph_full_summary.csv", index=False)

    print("\nWrote outputs to:", OUT_DIR)
    print("\nSUMMARY")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
