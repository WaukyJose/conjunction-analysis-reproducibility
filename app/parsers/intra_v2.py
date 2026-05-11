from pathlib import Path
import re
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DICT_DIR = BASE_DIR / "app" / "dictionaries"

sys.path.insert(0, str(DICT_DIR))

from halliday_intrasent_dic import INTRA_CLAUSE_CONJUNCTIONS


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


def extract_taxis(row):
    for col in ["path_2", "path_3", "path_4", "path_5"]:
        value = str(row.get(col, "")).strip()
        if value in {"paratactic", "hypotactic"}:
            return value
    return ""


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

    # Exclude frequency expressions: once a day/week/month/year.
    if connector == "once":
        after = sentence_lower[end_idx:end_idx + 25]
        if re.match(r"\s+a\s+(day|week|month|year)\b", after):
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
                "analysis_level": "intra_sentential_v2",
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