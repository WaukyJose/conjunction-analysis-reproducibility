from pathlib import Path
import re
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DICT_DIR = BASE_DIR / "app" / "dictionaries"

sys.path.insert(0, str(DICT_DIR))

from halliday_intrasent_dic import INTRA_CLAUSE_CONJUNCTIONS


PRIORITY_CONNECTOR_PATHS = {
    "and": ("Extension", "Addition", "paratactic"),
    "but": ("Extension", "Variation", "Subtractive", "paratactic"),
    "because": ("Enhancement", "Causal-Conditional", "Reason", "hypotactic"),
}


def flatten_dictionary(obj, path=None):
    if path is None:
        path = []

    rows = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            rows.extend(flatten_dictionary(value, path + [key]))

    elif isinstance(obj, list):
        for connector in obj:
            rows.append({
                "connector": str(connector).strip(),
                "path": path,
            })

    return rows


def build_connector_inventory():
    rows = flatten_dictionary(INTRA_CLAUSE_CONJUNCTIONS)
    df = pd.DataFrame(rows)

    df["connector_lower"] = df["connector"].str.lower().str.strip()
    df = df[df["connector_lower"] != ""].copy()

    for i in range(5):
        df[f"path_{i+1}"] = df["path"].apply(
            lambda x: x[i] if i < len(x) else ""
        )

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

    def priority_rank(row):
        priority_path = PRIORITY_CONNECTOR_PATHS.get(row["connector_lower"])
        if priority_path is None:
            return 1
        row_path = tuple(
            str(row.get(f"path_{i}", "")).strip()
            for i in range(1, 6)
            if str(row.get(f"path_{i}", "")).strip()
        )
        return 0 if row_path == priority_path else 1

    df["connector_priority"] = df.apply(priority_rank, axis=1)
    df = df.sort_values(
        ["connector_len", "connector_lower", "connector_priority"],
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



PROBLEMATIC_MULTIFUNCTIONAL_FORMS = {
    "and", "or", "as", "so", "but", "since", "when", "then", "while", "whereas", "rather"
}


def get_priming_annotation(connector, sentence_lower, start_idx, end_idx):
    """
    Diagnostic lexical-priming/context annotation for problematic multifunctional forms.
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

    # V2 validation documented in:
    # /Users/joselema/Conjunction_Research_V2/outputs/validation/rather_filter_recommendation.md
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

    if connector == "while":
        if re.match(r"\s+(i|we|you|he|she|they|it|there|people|students|children|the|a|an)\b", after):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "temporal_likely",
                "priming_confidence": "medium",
                "priming_notes": "While is followed by a subject-like element, suggesting a temporal subordinate clause.",
            }

    if re.match(r"\s+(i|we|you|he|she|they|it|there|people|students|children|the)\b", after):
        return {
            "is_problematic_multifunctional": 1,
            "priming_decision": "possibly_clause_like",
            "priming_confidence": "medium",
            "priming_notes": "Connector is followed by a subject-like element.",
        }

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

    if connector == "while":
        if re.match(r"\s+\w+ing\b", after):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "temporal_likely",
                "priming_confidence": "medium",
                "priming_notes": "While is followed by a present participle/V-ing form.",
            }

    if connector in {"while", "whereas"}:
        if re.search(r"\b(some|others|whereas|on the other hand|in contrast|however)\b", full_window):
            return {
                "is_problematic_multifunctional": 1,
                "priming_decision": "contrastive_likely",
                "priming_confidence": "medium",
                "priming_notes": f"{connector} appears in a contrastive local context.",
            }

    return {
        "is_problematic_multifunctional": 1,
        "priming_decision": "ambiguous",
        "priming_confidence": "low",
        "priming_notes": "Problematic multifunctional form; no strong local cue detected.",
    }


def is_priming_supported_case(connector, priming_decision):
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

    # Exclude IELTS prompt formula "agree or disagree".
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

        # Ported from the V2 research validation: exclude only audited
        # "formerly/previously" adjectival uses, not broad once clauses.
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

            if hit["is_priming_supported"] != 1:
                continue

            hit["analysis_level"] = "intra_sentential_supported_v2"

            hits.append(hit)
            used_spans.append((start_idx, end_idx))

    return hits


def analyse_text(text, text_id="text_1", group=""):
    connector_df = build_connector_inventory()
    sentences = split_sentences(text)

    rows = []

    for i, sent in enumerate(sentences):
        hits = detect_intra_markers(sent, connector_df)

        for hit in hits:
            rows.append({
                "text_id": text_id,
                "group": group,
                "sentence_index": i,
                **hit,
            })

    return pd.DataFrame(rows)


def analyse_file(input_file, output_file=None):
    input_file = Path(input_file)
    text = input_file.read_text(encoding="utf-8", errors="replace")

    df = analyse_text(text, text_id=input_file.stem)

    word_count_text = len(re.findall(r"\b\w+\b", text))
    sentence_count_text = len(split_sentences(text))

    if not df.empty:
        df["word_count_text"] = word_count_text
        if sentence_count_text is not None:
            df["sentence_count_text"] = sentence_count_text

    if output_file:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)

    return df
