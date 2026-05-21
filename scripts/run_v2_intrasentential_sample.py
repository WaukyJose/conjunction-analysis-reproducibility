from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_filtered"
DICT_FILE = BASE_DIR / "outputs" / "dictionary_audit" / "v2_recursive_dictionary_inventory.csv"
OUT_DIR = BASE_DIR / "outputs" / "v2_intrasentential_sample"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_N = 1000
RANDOM_SEED = 42

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
}


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


def load_intra_connectors():
    df = pd.read_csv(DICT_FILE)

    df = df[
        (df["level"] == "intra_sentential")
        & (df["include_main_v2"] == True)
    ].copy()

    df["connector_lower"] = df["connector_lower"].fillna("").str.strip()
    df = df[df["connector_lower"] != ""]

    # Longest first: "as soon as" before "as"
    df["connector_len"] = df["connector_lower"].str.split().str.len()
    df = df.sort_values(["connector_len", "connector_lower"], ascending=[False, True])

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


def is_risky_false_positive(connector, sentence_lower, start_idx, end_idx):
    """
    Conservative filters for obvious non-intra-clausal cases.
    These are intentionally simple at sample stage.
    """

    # Do not count sentence-initial markers as intra-sentential.
    if is_sentence_initial_match(sentence_lower, start_idx):
        return True

    # Exclude existential/deictic "there".
    if connector == "there":
        return True

    # Exclude deictic/location "here".
    if connector == "here":
        return True

    # Exclude "this is" as formulaic/anaphoric rather than intra-clausal conjunction.
    if connector == "this is":
        return True

    # Exclude high-risk connectors that are almost always false positives.
    risky_exact_exclusions = {
        "that",
        "by",
        "like",
        "through",
        "using",
        "especially",
        "the way",
    }
    if connector in risky_exact_exclusions:
        return True

    # Exclude bare "as" when it is part of larger formulaic/comparative expressions.
    if connector == "that":
        before = sentence_lower[max(0, start_idx - 40):start_idx]
        if re.search(r"\b(say|says|said|think|thinks|thought|believe|believes|know|knows|knew|show|shows|showed|means?)\s+$", before):
            return True

    # Exclude "like" as verb/preposition in common patterns.
    if connector == "like":
        before = sentence_lower[max(0, start_idx - 20):start_idx]
        after = sentence_lower[end_idx:end_idx + 30]
        if re.search(r"\b(i|you|we|they|he|she|people|students)\s+$", before):
            return True
        if re.match(r"\s+(a|an|the|this|that|my|your|his|her|their|our)\b", after):
            return True

    # Exclude bare "as" when it is prepositional, comparative, or part of a larger fixed phrase.
    if connector == "as":
        full_window = sentence_lower[max(0, start_idx - 35):end_idx + 35]
        before = sentence_lower[max(0, start_idx - 35):start_idx]
        after = sentence_lower[end_idx:end_idx + 35]
        # Exclude "such as" when bare "as" is matched.
        if re.search(r"\bsuch\s+$", before):
            return True

        # Exclude "as well" / "as well as".
        if re.match(r"\s+well\b", after):
            return True

        # Exclude role/classification uses: "as a/an/the..."
        if re.match(r"\s+(a|an|the|part|only|lower|upper|middle)\b", after):
            return True

        fixed_as_phrases = [
            "as well as",
            "as soon as",
            "as if",
            "as though",
        ]
        if any(phrase in full_window for phrase in fixed_as_phrases):
            return True
        # Comparative pattern: as friendly as, as important as, etc.
        if re.search(r"\bas\s+\w+\s+as\b", full_window):
            return True
        # Role/prepositional pattern: end up as, come across as, looked at X as, serve as, work as, act as.
        if re.search(
            r"\b(end up|ended up|come across|came across|look|looked|looks|see|saw|seen|serve|served|serves|work|worked|works|act|acted|acts|use|used|uses)\s+"
            r"(?:\w+\s+){0,4}as\s*$",
            before + "as",
        ):
            return True
        # If followed by a determiner/noun phrase, it is often role/prepositional: as a teacher, as an example.
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

    # Exclude IELTS prompt formula "agree or disagree".
    if connector == "or":
        full_window = sentence_lower[max(0, start_idx - 25):end_idx + 25]
        if "agree or disagree" in full_window:
            return True

    # Exclude "too" as intensifier rather than additive connector.
    if connector == "too":
        return True

    # Exclude sentence-internal "also" as additive adverb rather than clause-linking taxis.
    if connector == "also":
        return True

    # Exclude frequency expressions: once a day/week/month/year.
    if connector == "once":
        after = sentence_lower[end_idx:end_idx + 25]
        if re.match(r"\s+a\s+(day|week|month|year)\b", after):
            return True

    # Exclude place-name artefact: So Paulo / São Paulo.
    if connector == "so":
        after = sentence_lower[end_idx:end_idx + 15]
        if re.match(r"\s+paulo\b", after):
            return True

    # Exclude nominal time expressions with "a while":
    # e.g., "after a while", "for a while", "a while ago".
    if connector == "while":
        before = sentence_lower[max(0, start_idx - 15):start_idx]
        if before.rstrip().endswith("a"):
            return True
        if re.search(r"\b(after|for|in|within)\s+a\s+$", before):
            return True

    return False


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

    sample_n = min(SAMPLE_N, len(df))
    sample = df.sample(n=sample_n, random_state=RANDOM_SEED).copy()

    rows = []

    for _, r in sample.iterrows():
        text_id = r[spec["id_col"]]
        group_value = r[spec["group_col"]]
        text = r[spec["text_col"]]

        sentences = split_sentences(text)

        for i, sent in enumerate(sentences):
            hits = detect_intra_markers(sent, connector_df)

            for hit in hits:
                rows.append({
                    "corpus": corpus,
                    "text_id": text_id,
                    "group": group_value,
                    "sentence_index": i,
                    **hit,
                    "word_count_text": r.get("wc_preserve", None),
                    "source_file": str(spec["file"]),
                    "algorithm_notes": (
                        "V2 intra-sentential sample: detects dictionary items within sentences, "
                        "excluding sentence-initial discourse markers and selected obvious false positives."
                    ),
                })

    return pd.DataFrame(rows), sample_n


def main():
    connector_df = load_intra_connectors()

    all_cases = []
    summary_rows = []

    print("Loaded intra-sentential connectors:", connector_df["connector_lower"].nunique())

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

    if not out_cases.empty:
        out_cases["taxis"] = out_cases.apply(extract_taxis, axis=1)

    out_cases.to_csv(OUT_DIR / "v2_intrasentential_sample_cases.csv", index=False)
    out_summary.to_csv(OUT_DIR / "v2_intrasentential_sample_summary.csv", index=False)

    if not out_cases.empty:
        macro_summary = (
            out_cases.groupby(["corpus", "macro_category"])
            .size()
            .reset_index(name="n_cases")
        )
        macro_summary.to_csv(OUT_DIR / "v2_intrasentential_sample_macro_summary.csv", index=False)

        taxis_summary = (
            out_cases.groupby(["corpus", "taxis"])
            .size()
            .reset_index(name="n_cases")
        )
        taxis_summary.to_csv(
            OUT_DIR / "v2_intrasentential_sample_taxis_summary.csv",
            index=False
        )

        taxis_macro_summary = (
            out_cases.groupby(["corpus", "taxis", "macro_category"])
            .size()
            .reset_index(name="n_cases")
        )
        taxis_macro_summary.to_csv(
            OUT_DIR / "v2_intrasentential_sample_taxis_macro_summary.csv",
            index=False
        )

    print("\nWrote outputs to:", OUT_DIR)
    print("\nSUMMARY")
    print(out_summary.to_string(index=False))


if __name__ == "__main__":
    main()
