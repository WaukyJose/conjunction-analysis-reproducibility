from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_filtered"
DICT_FILE = BASE_DIR / "outputs" / "dictionary_audit" / "v2_recursive_dictionary_inventory.csv"
OUT_DIR = BASE_DIR / "outputs" / "v2_interparagraph_sample"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_N = 200
RANDOM_SEED = 42

# V2 true inter-paragraph analysis is restricted to GiG because GiG preserves newline paragraph boundaries.
DATASET = {
    "corpus": "GiG",
    "file": DATA_DIR / "gig_v2_filtered.csv",
    "id_col": "text_id",
    "text_col": "text_clean_preserveCase",
    "group_col": "year_group",
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


def process_gig_sample(connector_df):
    spec = DATASET
    df = pd.read_csv(spec["file"], low_memory=False)

    # Only texts with explicit newline paragraph boundaries.
    df["has_real_paragraph_boundary"] = df[spec["text_col"]].apply(paragraph_has_real_boundary)
    df = df[df["has_real_paragraph_boundary"]].copy()

    sample_n = min(SAMPLE_N, len(df))
    sample = df.sample(n=sample_n, random_state=RANDOM_SEED).copy()

    rows = []

    for _, r in sample.iterrows():
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
                    "corpus": spec["corpus"],
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
                        "V2 inter-paragraph: GiG only; detects first discourse-marker sequence "
                        "at the beginning of paragraphs with explicit newline boundaries. "
                        "Stance_Markers excluded from main analysis."
                    ),
                })

    return pd.DataFrame(rows), sample_n, len(df)


def main():
    connector_df = load_interparagraph_connectors()

    print("Loaded inter-paragraph connectors:", connector_df["connector_lower"].nunique())

    cases, sample_n, eligible_n = process_gig_sample(connector_df)

    summary = pd.DataFrame([{
        "corpus": DATASET["corpus"],
        "eligible_texts_with_newline_boundaries": eligible_n,
        "sample_n_texts": sample_n,
        "detected_cases": len(cases),
        "detected_cases_per_text": round(len(cases) / sample_n, 4) if sample_n else 0,
    }])

    cases.to_csv(OUT_DIR / "v2_interparagraph_gig_sample_cases.csv", index=False)
    summary.to_csv(OUT_DIR / "v2_interparagraph_gig_sample_summary.csv", index=False)

    if not cases.empty:
        macro_summary = (
            cases.groupby(["corpus", "macro_category"])
            .size()
            .reset_index(name="n_cases")
        )
        macro_summary.to_csv(OUT_DIR / "v2_interparagraph_gig_sample_macro_summary.csv", index=False)

    print("\nWrote outputs to:", OUT_DIR)
    print("\nSUMMARY")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
