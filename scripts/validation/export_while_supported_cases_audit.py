from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_FILE = OUT_DIR / "while_supported_cases_audit.csv"

OUTPUT_COLUMNS = [
    "corpus",
    "text_id",
    "detected_item",
    "macro_category",
    "path_2",
    "path_3",
    "path_4",
    "path_5",
    "taxis",
    "priming_decision",
    "priming_confidence",
    "priming_reason",
    "sentence",
    "left_context",
    "right_context",
    "previous_token",
    "next_token",
    "following_3_tokens",
    "suggested_pattern",
    "manual_label",
    "notes",
]

PRONOUNS = {
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "me",
    "him",
    "her",
    "us",
    "them",
    "there",
}

DETERMINERS = {
    "a",
    "an",
    "the",
    "my",
    "your",
    "his",
    "her",
    "its",
    "our",
    "their",
    "some",
    "any",
    "each",
    "every",
}

DEMONSTRATIVES = {"this", "that", "these", "those"}
COMMON_NOUN_CLAUSE_STARTERS = {
    "people",
    "students",
    "children",
    "parents",
    "teachers",
    "workers",
    "companies",
    "government",
    "society",
    "team",
    "system",
    "output",
    "result",
    "person",
    "man",
    "woman",
}


def as_int(value):
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def find_while_span(row):
    sentence = str(row.get("sentence", ""))
    start = as_int(row.get("connector_start_char"))
    end = as_int(row.get("connector_end_char"))

    if start is not None and end is not None:
        if 0 <= start < end <= len(sentence):
            if sentence[start:end].lower() == "while":
                return start, end

    match = re.search(r"\bwhile\b", sentence, flags=re.IGNORECASE)
    if match:
        return match.start(), match.end()

    return None, None


def tokenize(text):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", str(text).lower())


def context_fields(row):
    sentence = str(row.get("sentence", ""))
    start, end = find_while_span(row)

    if start is None or end is None:
        return "", "", "", "", ""

    left_context = sentence[max(0, start - 80):start]
    right_context = sentence[end:end + 120]
    previous_tokens = tokenize(left_context)
    following_tokens = tokenize(right_context)

    previous_token = previous_tokens[-1] if previous_tokens else ""
    next_token = following_tokens[0] if following_tokens else ""
    following_3_tokens = " ".join(following_tokens[:3])

    return (
        left_context,
        right_context,
        previous_token,
        next_token,
        following_3_tokens,
    )


def is_noun_phrase_candidate(left_context, right_context, previous_token, following_3_tokens):
    left_context = str(left_context).lower()
    right_context = str(right_context).lower()
    previous_token = str(previous_token).lower().strip()
    following_3_tokens = str(following_3_tokens).lower().strip()

    if previous_token == "a":
        return True

    local = f"{left_context}while{right_context}"
    if re.search(r"\b(for|in)\s+a\s*,?\s*while\b", local):
        return True
    if re.search(r"\bonce\s+in\s+a\s+while\b", local):
        return True
    if re.search(r"\b(for|in)\s+awhile\b", local):
        return True
    if following_3_tokens.startswith("ago"):
        return True

    return False


def suggest_pattern(row):
    previous_token = row["previous_token"]
    next_token = str(row["next_token"]).lower().strip()
    following_3_tokens = row["following_3_tokens"]

    if is_noun_phrase_candidate(
        row["left_context"],
        row["right_context"],
        previous_token,
        following_3_tokens,
    ):
        return "exclude_while_noun_phrase_candidate"

    if next_token.endswith("ing") and len(next_token) > 4:
        return "keep_while_ving_clause"

    if (
        next_token in PRONOUNS
        or next_token in DETERMINERS
        or next_token in DEMONSTRATIVES
        or next_token in COMMON_NOUN_CLAUSE_STARTERS
    ):
        return "keep_while_subject_clause"

    return "review"


def build_audit(df):
    supported_while = df[
        (df["is_priming_supported"] == 1)
        & (df["detected_item"].astype(str).str.lower().str.strip() == "while")
    ].copy()

    if supported_while.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    contexts = supported_while.apply(context_fields, axis=1, result_type="expand")
    supported_while["left_context"] = contexts[0]
    supported_while["right_context"] = contexts[1]
    supported_while["previous_token"] = contexts[2]
    supported_while["next_token"] = contexts[3]
    supported_while["following_3_tokens"] = contexts[4]
    supported_while["suggested_pattern"] = supported_while.apply(suggest_pattern, axis=1)
    supported_while["manual_label"] = ""
    supported_while["notes"] = ""

    for column in OUTPUT_COLUMNS:
        if column not in supported_while.columns:
            supported_while[column] = ""

    return supported_while[OUTPUT_COLUMNS].sort_values(
        ["corpus", "text_id"],
        ascending=[True, True],
        kind="mergesort",
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    required = {"is_priming_supported", "detected_item"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    audit = build_audit(df)
    audit.to_csv(OUT_FILE, index=False)

    print("Input path:", INPUT_FILE)
    print("Output path:", OUT_FILE)
    print("Supported while cases:", len(audit))
    print("\nCounts by suggested_pattern:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["suggested_pattern"].value_counts().to_string())

    print("\nFirst 30 rows:")
    preview_cols = [
        "corpus",
        "text_id",
        "suggested_pattern",
        "previous_token",
        "next_token",
        "following_3_tokens",
        "sentence",
    ]
    print(audit[preview_cols].head(30).to_string(index=False))

    print("\nExclude noun-phrase candidates:")
    exclude_rows = audit[
        audit["suggested_pattern"] == "exclude_while_noun_phrase_candidate"
    ]
    if exclude_rows.empty:
        print("(none)")
    else:
        print(exclude_rows[preview_cols].head(100).to_string(index=False))


if __name__ == "__main__":
    main()
