from pathlib import Path
import re
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DICT_DIR = BASE_DIR / "app" / "dictionaries"

sys.path.insert(0, str(DICT_DIR))

from halliday_paragraph_dict import HALLIDAY_CONJUNCTIONS


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
    rows = flatten_dictionary(HALLIDAY_CONJUNCTIONS)
    df = pd.DataFrame(rows)

    df["connector_lower"] = df["connector"].str.lower().str.strip()
    df = df[df["connector_lower"] != ""].copy()

    for i in range(5):
        df[f"path_{i+1}"] = df["path"].apply(
            lambda x: x[i] if i < len(x) else ""
        )

    # Exclude paragraph Stance_Markers from main V2 analysis.
    df = df[
        ~(
            (df["path_1"] == "Extension")
            & (df["path_2"] == "Stance_Markers")
        )
    ].copy()

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

    df["connector_len"] = df["connector_lower"].str.split().str.len()
    df = df.sort_values(["connector_len", "connector_lower"], ascending=[False, True])

    return df


def split_paragraphs(text):
    """
    True paragraph splitter based on newline boundaries.
    This parser should be used only when the input text preserves paragraph breaks.
    """
    if not isinstance(text, str):
        return []

    text = text.strip()
    if not text:
        return []

    parts = re.split(r"\n+", text)
    parts = [re.sub(r"\s+", " ", p.strip()) for p in parts]
    return [p for p in parts if p]


def has_real_paragraph_boundary(text):
    return isinstance(text, str) and "\n" in text.strip()


def normalise_paragraph_start(paragraph):
    p = paragraph.strip()

    p = re.sub(r"^[-•\*\s]+", "", p)
    p = re.sub(r"^\(?[0-9]+[\).\:\-]\s*", "", p)
    p = re.sub(r"^[A-Za-z][\).\:\-]\s+", "", p)
    p = re.sub(r"^[\"'“”‘’\(\[\{]+", "", p)

    return p.strip()


def detect_paragraph_initial_marker(paragraph, connector_df):
    start = normalise_paragraph_start(paragraph)
    start_lower = start.lower()

    for _, row in connector_df.iterrows():
        connector = row["connector_lower"]
        pattern = r"^" + re.escape(connector) + r"(\b|[,\.;:\?!])"

        if re.search(pattern, start_lower):

            if connector == "in case" and re.match(r"^in case stud(y|ies)\b", start_lower):
                continue

            if connector == "so" and re.fullmatch(r"so[\.,;:!\?]?", start_lower.strip()):
                continue

            return {
                "detected_item": row["connector"],
                "macro_category": row["path_1"],
                "path_2": row.get("path_2", ""),
                "path_3": row.get("path_3", ""),
                "path_4": row.get("path_4", ""),
                "path_5": row.get("path_5", ""),
                "paragraph_start_cleaned": start,
            }

    return None


def analyse_text(text, text_id="text_1", group=""):
    connector_df = build_connector_inventory()

    if not has_real_paragraph_boundary(text):
        return pd.DataFrame()

    paragraphs = split_paragraphs(text)
    rows = []

    for i, paragraph in enumerate(paragraphs):
        if i == 0:
            continue

        hit = detect_paragraph_initial_marker(paragraph, connector_df)

        if hit:
            rows.append({
                "text_id": text_id,
                "group": group,
                "paragraph_index": i,
                "previous_paragraph": paragraphs[i - 1],
                "current_paragraph": paragraph,
                **hit,
                "paragraph_count_text": len(paragraphs),
                "analysis_level": "inter_paragraph_v2_true_boundaries",
            })

    return pd.DataFrame(rows)


def analyse_file(input_file, output_file=None):
    input_file = Path(input_file)
    text = input_file.read_text(encoding="utf-8", errors="replace")

    df = analyse_text(text, text_id=input_file.stem)

    word_count_text = len(re.findall(r"\b\w+\b", text))
    sentence_count_text = None

    if not df.empty:
        df["word_count_text"] = word_count_text
        if sentence_count_text is not None:
            df["sentence_count_text"] = sentence_count_text

    if output_file:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)

    return df