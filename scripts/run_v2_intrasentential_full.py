from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_filtered"
DICT_FILE = BASE_DIR / "outputs" / "dictionary_audit" / "v2_recursive_dictionary_inventory.csv"

OUT_DIR = BASE_DIR / "outputs" / "v2_intrasentential_full"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROBLEMATIC_MULTIFUNCTIONAL_FORMS = {
    "and",
    "or",
    "as",
    "since",
    "while",
    "when",
    "then",
    "so",
    "but",
    "yet",
    "still",
    "however",
    "thus",
    "whereas",
    "rather",
}

COORDINATION_PRECEDENCE = {
    ("and", "Extension", "Addition"),
    ("but", "Extension", "Adversative"),
    ("or", "Extension", "Variation"),
}

DATASETS = {
    "EFCAMDAT": {
        "file": DATA_DIR / "efcamdat_v2_filtered.csv",
        "id_col": "writing_id",
        "text_col": "text_clean_preserveCase",
        "group_col": "cefr",
    },
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


def load_intra_connectors():
    df = pd.read_csv(DICT_FILE)

    df = df[
        (df["level"] == "intra_sentential")
        & (df["include_main_v2"] == True)
    ].copy()

    df["connector_lower"] = df["connector_lower"].fillna("").str.strip()
    df = df[df["connector_lower"] != ""]

    risky_exact_exclusions = {
        "there",
        "here",
        "this is",
        "that",
        "by",
        "like",
        "through",
        "using",
        "especially",
        "the way",
        "too",
        "also",
    }

    df = df[~df["connector_lower"].isin(risky_exact_exclusions)].copy()

    df["connector_len"] = df["connector_lower"].str.split().str.len()
    df["coordination_precedence"] = df.apply(
        lambda row: 0
        if (
            row["connector_lower"],
            row.get("path_1", ""),
            row.get("path_2", ""),
        )
        in COORDINATION_PRECEDENCE
        else 1,
        axis=1,
    )
    df = df.sort_values(
        ["connector_len", "connector_lower", "coordination_precedence"],
        ascending=[False, True, True],
        kind="mergesort",
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


def is_sentence_initial_match(sentence, start_idx):
    prefix = sentence[:start_idx].strip()
    prefix = re.sub(r"^[\"'“”‘’\(\[\{]+", "", prefix)
    prefix = re.sub(r"^[-•\*\s]+", "", prefix)
    prefix = re.sub(r"^\(?[0-9]+[\).\:\-]\s*", "", prefix)
    return prefix == ""


def extract_taxis(row):
    for col in ["path_2", "path_3", "path_4", "path_5"]:
        value = str(row.get(col, "")).strip()
        if value in {"paratactic", "hypotactic"}:
            return value
    return ""


def get_priming_annotation(connector, sentence_lower, start_idx, end_idx):
    """
    Diagnostic lexical-priming/context annotation for problematic multifunctional forms.
    This does not filter cases; it only labels likely contextual function.
    """

    if connector not in PROBLEMATIC_MULTIFUNCTIONAL_FORMS:
        return {
            "is_problematic_multifunctional": 0,
            "priming_decision": "not_required",
            "priming_confidence": "high",
            "priming_notes": "Connector is not in the problematic multifunctional list.",
        }

    before = sentence_lower[max(0, start_idx - 60):start_idx]
    after = sentence_lower[end_idx:end_idx + 80]
    full_window = sentence_lower[max(0, start_idx - 60):end_idx + 80]

    # Targeted supported-output filter from outputs/validation/rather_filter_recommendation.md.
    if connector == "rather":
        if re.search(r"\brather\s+than\b|\bor\s+rather\b|\bbut\s+rather\b", full_window):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "replacive_likely",
                "priming_confidence": "medium",
                "priming_notes": "Rather appears in a validated replacive context.",
            }

        return {
            "is_problematic_multifunctional": 1,
            "priming_decision": "ambiguous",
            "priming_confidence": "low",
            "priming_notes": "Bare rather is excluded from the supported subset unless in rather than, or rather, or but rather.",
        }

    # Stronger clause-like cue for "and" followed by subject-like element.
    if connector == "and":
        after_stripped = after.strip()

        if re.match(r"^(i|we|you|he|she|they|it|there)\b", after_stripped):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "clause_like",
                "priming_confidence": "medium",
                "priming_notes": "And is followed by a pronoun/subject-like element.",
            }

        if re.match(r"(am|is|are|was|were|have|has|had|do|does|did|can|could|will|would|should|may|might|must)\b", after_stripped):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "verb_phrase_like",
                "priming_confidence": "medium",
                "priming_notes": "And is followed by an auxiliary or finite verb-like element.",
            }

    # Phrase-like coordination patterns for and/or.
    if connector in {"and", "or"}:
        if re.search(r"\b\w+\s+$", before) and re.match(
            r"\s+(a|an|the|this|that|these|those|my|your|his|her|their|our)?\s*\w+\b",
            after,
        ):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "possibly_phrase_like",
                "priming_confidence": "low",
                "priming_notes": f"{connector} may link words/phrases rather than full clauses.",
            }

    # Temporal clause cue for while + subject-like element.
    if connector == "while":
        if re.match(r"\s+(i|we|you|he|she|they|it|there|people|students|children|the|a|an)\b", after):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "temporal_likely",
                "priming_confidence": "medium",
                "priming_notes": "While is followed by a subject-like element, suggesting a temporal subordinate clause.",
            }

    # Clause-like cue: connector followed by pronoun/subject-like element.
    if re.match(r"\s+(i|we|you|he|she|they|it|there|people|students|children|the)\b", after):
        return {
            "is_problematic_multifunctional": 1,
            "priming_decision": "possibly_clause_like",
            "priming_confidence": "medium",
            "priming_notes": "Connector is followed by a subject-like element.",
        }

    # Temporal cue for since + explicit time expression.
    if connector == "since":
        if re.match(
            r"\s+(\d{4}|[0-9]+|then|yesterday|last\s+\w+|that\s+time|the\s+\w+\s+(day|week|month|year))\b",
            after,
        ):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "temporal_likely",
                "priming_confidence": "medium",
                "priming_notes": "Since is followed by an explicit time-like expression.",
            }

    # Temporal cue for while + V-ing.
    if connector == "while":
        if re.match(r"\s+\w+ing\b", after):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "temporal_likely",
                "priming_confidence": "medium",
                "priming_notes": "While is followed by a present participle/V-ing form.",
            }

    # Contrastive cue for while/whereas.
    if connector in {"while", "whereas"}:
        if re.search(r"\b(some|others|whereas|on the other hand|in contrast|however)\b", full_window):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "contrastive_likely",
                "priming_confidence": "medium",
                "priming_notes": f"{connector} appears in a contrastive local context.",
            }

    # Default for problematic form.
    return {
        "is_problematic_multifunctional": 1,
        "priming_decision": "ambiguous",
        "priming_confidence": "low",
        "priming_notes": "Problematic multifunctional form; no strong local cue detected.",
    }


def is_priming_supported_case(connector, priming_decision):
    """
    Decide whether a detected intra-sentential case belongs to the stricter
    priming-supported subset.

    Broad output keeps all detections.
    Strict output uses this flag.
    """

    connector = str(connector).lower().strip()
    priming_decision = str(priming_decision).strip()

    always_supported = {
        "not_required",
        "clause_like",
        "verb_phrase_like",
        "temporal_likely",
        "contrastive_likely",
        "replacive_likely",
    }

    selected_possible_clause_like = {
        "as",
        "so",
        "but",
        "since",
        "when",
        "then",
    }

    if priming_decision in always_supported:
        return 1

    if (
        priming_decision == "possibly_clause_like"
        and connector in selected_possible_clause_like
    ):
        return 1

    return 0


def is_risky_false_positive(connector, sentence_lower, start_idx, end_idx):
    # Do not count sentence-initial markers as intra-sentential.
    if is_sentence_initial_match(sentence_lower, start_idx):
        return True

    # Exclude bare "as" when it is prepositional, comparative, or part of a larger fixed phrase.
    if connector == "as":
        full_window = sentence_lower[max(0, start_idx - 35):end_idx + 35]
        before = sentence_lower[max(0, start_idx - 35):start_idx]
        after = sentence_lower[end_idx:end_idx + 35]

        fixed_as_phrases = [
            "as well as",
            "as soon as",
            "as if",
            "as though",
        ]

        if any(phrase in full_window for phrase in fixed_as_phrases):
            return True

        if re.search(r"\bas\s+\w+\s+as\b", full_window):
            return True

        if re.search(
            r"\b(end up|ended up|come across|came across|look|looked|looks|see|saw|seen|serve|served|serves|work|worked|works|act|acted|acts|use|used|uses)\s+"
            r"(?:\w+\s+){0,4}as\s*$",
            before + "as",
        ):
            return True

        if re.match(r"\s+(a|an|the|this|that|my|your|his|her|their|our)\b", after):
            return True

    # Exclude fixed expression "more and more".
    if connector == "and":
        full_window = sentence_lower[max(0, start_idx - 15):end_idx + 15]
        if "more and more" in full_window:
            return True

    # Exclude fixed expression "in and out".
    if connector == "and":
        before = sentence_lower[max(0, start_idx - 10):start_idx]
        after = sentence_lower[end_idx:end_idx + 10]
        if before.rstrip().endswith("in") and after.lstrip().startswith("out"):
            return True

    # Exclude IELTS/essay prompt formula "agree or disagree".
    if connector == "or":
        full_window = sentence_lower[max(0, start_idx - 25):end_idx + 25]
        if "agree or disagree" in full_window:
            return True

    # Exclude noun-phrase uses of "while" meaning a period of time.
    if connector == "while":
        window = sentence_lower[max(0, start_idx - 40):end_idx + 40]
        window = re.sub(r"\s+", " ", window)
        a_while = r"a\s*[,;:]?\s*while"
        awhile = r"awhile"

        while_np_patterns = [
            rf"\bafter\s+(?:{a_while}|{awhile})\b",
            rf"\bfor\s+(?:{a_while}|{awhile})\b",
            rf"\bin\s+(?:{a_while}|{awhile})\b",
            rf"\bonce\s+in\s+(?:{a_while}|{awhile})\b",
            rf"\bit\s+(?:has|had)\s+been\s+(?:{a_while}|{awhile})\b",
            rf"\bit'?s\s+been\s+(?:{a_while}|{awhile})\b",
            rf"\bduring\s+{a_while}\b",
            rf"\b(?:take|takes|took|taken|taking)\s+{a_while}\b",
        ]

        if any(re.search(pattern, window) for pattern in while_np_patterns):
            return True

    # Exclude frequency expressions: once a day/week/month/year.
    if connector == "once":
        after = sentence_lower[end_idx:end_idx + 25]
        full_window = sentence_lower[max(0, start_idx - 15):end_idx + 25]
        if re.search(r"\bonce\s+in\s+(?:a\s+while|awhile)\b", full_window):
            return True

        if re.match(r"\s+a\s+(day|week|month|year)\b", after):
            return True

        # Validation: outputs/validation/once_supported_cases_audit.csv.
        # Exclude "formerly/previously" adjectival uses only for audited whitelist items.
        ONCE_FORMERLY_ADJ_WHITELIST = {
            "wealthy",
            "prestigious",
            "famous",
            "luxurious",
            "successful",
            "constant",
            "beautiful",
            "vibrant",
            "proud",
            "pure",
            "strong",
            "important",
            "powerful",
            "popular",
            "great",
            "old",
            "former",
            "dominant",
        }
        next_token_match = re.match(r"[\s-]+([a-z]+)\b", after)
        if (
            next_token_match
            and next_token_match.group(1) in ONCE_FORMERLY_ADJ_WHITELIST
        ):
            return True

    # Exclude place-name artefact: So Paulo.
    if connector == "so":
        after = sentence_lower[end_idx:end_idx + 15]
        if re.match(r"\s+paulo\b", after):
            return True

    return False


def detect_intra_markers(sentence, connector_df):
    hits = []
    sentence_lower = sentence.lower()
    used_spans = []

    for _, row in connector_df.iterrows():
        connector = row["connector_lower"]
        pattern = r"(?<!\w)" + re.escape(connector) + r"(?!\w)"

        for match in re.finditer(pattern, sentence_lower):
            start_idx, end_idx = match.span()

            # Avoid overlapping matches once a longer connector has been accepted.
            if any(not (end_idx <= s or start_idx >= e) for s, e in used_spans):
                continue

            if is_risky_false_positive(connector, sentence_lower, start_idx, end_idx):
                continue

            hit = {
                "detected_item": row["connector"],
                "macro_category": row["path_1"],
                "path_2": row.get("path_2", ""),
                "path_3": row.get("path_3", ""),
                "path_4": row.get("path_4", ""),
                "path_5": row.get("path_5", ""),
                "connector_start_char": start_idx,
                "connector_end_char": end_idx,
                "sentence": sentence,
            }

            hit["taxis"] = extract_taxis(hit)
            priming = get_priming_annotation(
                connector=connector,
                sentence_lower=sentence_lower,
                start_idx=start_idx,
                end_idx=end_idx,
            )
            hit.update(priming)
            hit["is_priming_supported"] = is_priming_supported_case(
                connector=connector,
                priming_decision=hit["priming_decision"],
            )

            hits.append(hit)
            used_spans.append((start_idx, end_idx))

    return hits


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
            hits = detect_intra_markers(sent, connector_df)

            for hit in hits:
                text_case_count += 1

                case_rows.append({
                    "corpus": corpus,
                    "text_id": text_id,
                    "group": group_value,
                    "sentence_index": i,
                    **hit,
                    "word_count_text": word_count,
                    "sentence_count_text": n_sentences,
                    "source_file": str(spec["file"]),
                    "algorithm_notes": (
                        "V2 full intra-sentential: detects dictionary items within sentences, "
                        "extracts taxis dynamically, and excludes selected lexical/contextual false positives. "
                        "Broad and/or coordination remains an approximation rather than full clause parsing."
                    ),
                })

        text_rows.append({
            "corpus": corpus,
            "text_id": text_id,
            "group": group_value,
            "word_count_text": word_count,
            "sentence_count_text": n_sentences,
            "intra_sentential_cases": text_case_count,
            "intra_sentential_per_100_words": (
                text_case_count / word_count * 100
                if pd.notna(word_count) and word_count > 0 else None
            ),
            "intra_sentential_per_1000_words": (
                text_case_count / word_count * 1000
                if pd.notna(word_count) and word_count > 0 else None
            ),
        })

    return pd.DataFrame(case_rows), pd.DataFrame(text_rows)


def build_text_level_indices(all_cases, all_texts):
    """
    Build text-level raw and per-1,000-word indices for:
    taxis × macro category.
    """
    if all_cases.empty:
        return all_texts.copy()

    counts = (
        all_cases.groupby(["corpus", "text_id", "taxis", "macro_category"])
        .size()
        .reset_index(name="raw_count")
    )

    counts["index_name"] = (
        "intra_"
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
        "intra_paratactic_elaboration",
        "intra_paratactic_extension",
        "intra_paratactic_enhancement",
        "intra_hypotactic_elaboration",
        "intra_hypotactic_extension",
        "intra_hypotactic_enhancement",
    ]

    for col in expected:
        if col not in wide.columns:
            wide[col] = 0

    raw_cols = expected

    out = all_texts.merge(wide, on=["corpus", "text_id"], how="left")

    out[raw_cols] = out[raw_cols].fillna(0).astype(int)

    for col in raw_cols:
        out = out.rename(columns={col: f"{col}_raw"})

    for col in [f"{c}_raw" for c in raw_cols]:
        norm_col = col.replace("_raw", "_per_1000")
        out[norm_col] = (
            out[col] / out["word_count_text"] * 1000
        ).where(out["word_count_text"] > 0)

    return out


def save_outputs(all_cases, all_texts):
    all_cases.to_csv(OUT_DIR / "v2_intrasentential_full_cases.csv", index=False)
    all_texts.to_csv(OUT_DIR / "v2_intrasentential_full_text_counts.csv", index=False)

    text_indices = build_text_level_indices(all_cases, all_texts)
    text_indices.to_csv(OUT_DIR / "v2_intrasentential_full_text_indices.csv", index=False)

    corpus_summary = (
        all_texts.groupby("corpus")
        .agg(
            n_texts=("text_id", "count"),
            total_cases=("intra_sentential_cases", "sum"),
            mean_cases_per_text=("intra_sentential_cases", "mean"),
            median_cases_per_text=("intra_sentential_cases", "median"),
            mean_per_1000_words=("intra_sentential_per_1000_words", "mean"),
            median_per_1000_words=("intra_sentential_per_1000_words", "median"),
        )
        .reset_index()
    )
    corpus_summary.to_csv(OUT_DIR / "v2_intrasentential_full_corpus_summary.csv", index=False)

    macro_summary = (
        all_cases.groupby(["corpus", "macro_category"])
        .size()
        .reset_index(name="n_cases")
    )
    macro_summary.to_csv(OUT_DIR / "v2_intrasentential_full_macro_summary.csv", index=False)

    taxis_summary = (
        all_cases.groupby(["corpus", "taxis"])
        .size()
        .reset_index(name="n_cases")
    )
    taxis_summary.to_csv(OUT_DIR / "v2_intrasentential_full_taxis_summary.csv", index=False)

    taxis_macro_summary = (
        all_cases.groupby(["corpus", "taxis", "macro_category"])
        .size()
        .reset_index(name="n_cases")
    )
    taxis_macro_summary.to_csv(OUT_DIR / "v2_intrasentential_full_taxis_macro_summary.csv", index=False)

    item_summary = (
        all_cases.groupby(["corpus", "detected_item"])
        .size()
        .reset_index(name="n_cases")
        .sort_values(["corpus", "n_cases"], ascending=[True, False])
    )
    item_summary.to_csv(OUT_DIR / "v2_intrasentential_full_item_summary.csv", index=False)

    group_summary = (
        all_texts.groupby(["corpus", "group"])
        .agg(
            n_texts=("text_id", "count"),
            total_cases=("intra_sentential_cases", "sum"),
            mean_cases_per_text=("intra_sentential_cases", "mean"),
            median_cases_per_text=("intra_sentential_cases", "median"),
            mean_per_1000_words=("intra_sentential_per_1000_words", "mean"),
            median_per_1000_words=("intra_sentential_per_1000_words", "median"),
        )
        .reset_index()
    )
    group_summary.to_csv(OUT_DIR / "v2_intrasentential_full_group_summary.csv", index=False)

    return text_indices


def main():
    connector_df = load_intra_connectors()

    print("Loaded intra-sentential connectors:", connector_df["connector_lower"].nunique())
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

        cases.to_csv(OUT_DIR / f"v2_intrasentential_full_cases_{corpus}.csv", index=False)
        text_counts.to_csv(OUT_DIR / f"v2_intrasentential_full_text_counts_{corpus}.csv", index=False)

    all_cases = pd.concat(all_case_frames, ignore_index=True) if all_case_frames else pd.DataFrame()
    all_texts = pd.concat(all_text_frames, ignore_index=True) if all_text_frames else pd.DataFrame()

    text_indices = save_outputs(all_cases, all_texts)

    print("\n" + "=" * 80)
    print("FULL INTRA-SENTENTIAL V2 COMPLETE")
    print("Total cases:", len(all_cases))
    print("Total texts:", len(all_texts))
    print("Outputs saved to:", OUT_DIR)

    print("\nCorpus summary:")
    print(
        all_texts.groupby("corpus")
        .agg(
            n_texts=("text_id", "count"),
            total_cases=("intra_sentential_cases", "sum"),
            mean_per_1000=("intra_sentential_per_1000_words", "mean"),
            median_per_1000=("intra_sentential_per_1000_words", "median"),
        )
        .reset_index()
        .to_string(index=False)
    )

    print("\nTaxis × macro summary:")
    print(
        all_cases.groupby(["corpus", "taxis", "macro_category"])
        .size()
        .reset_index(name="n_cases")
        .to_string(index=False)
    )

    print("\nMean text-level indices per 1,000 words:")
    norm_cols = [c for c in text_indices.columns if c.endswith("_per_1000")]
    print(
        text_indices.groupby("corpus")[norm_cols]
        .mean()
        .reset_index()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
