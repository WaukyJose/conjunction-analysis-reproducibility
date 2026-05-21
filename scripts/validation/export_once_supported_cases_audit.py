from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_FILE = OUT_DIR / "once_supported_cases_audit.csv"

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

ADJECTIVE_WORDS = {
    "beautiful",
    "constant",
    "dominant",
    "famous",
    "former",
    "great",
    "important",
    "luxurious",
    "old",
    "popular",
    "powerful",
    "prestigious",
    "proud",
    "pure",
    "strong",
    "successful",
    "vibrant",
    "wealthy",
}

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


def as_int(value):
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def find_once_span(row):
    sentence = str(row.get("sentence", ""))
    start = as_int(row.get("connector_start_char"))
    end = as_int(row.get("connector_end_char"))

    if start is not None and end is not None:
        if 0 <= start < end <= len(sentence):
            if sentence[start:end].lower() == "once":
                return start, end

    match = re.search(r"\bonce\b", sentence, flags=re.IGNORECASE)
    if match:
        return match.start(), match.end()

    return None, None


def tokenize(text):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", str(text).lower())


def is_adjective_like(token):
    token = str(token).lower().strip()
    return token in ADJECTIVE_WORDS


def has_hyphenated_once_adjective(right_context):
    return bool(
        re.match(
            r"\s*-\s*(" + "|".join(re.escape(word) for word in sorted(ADJECTIVE_WORDS)) + r")\b",
            str(right_context).lower(),
        )
    )


def context_fields(row):
    sentence = str(row.get("sentence", ""))
    start, end = find_once_span(row)

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


def suggest_pattern(next_token, right_context):
    next_token = str(next_token).lower().strip()
    if is_adjective_like(next_token) or has_hyphenated_once_adjective(right_context):
        return "exclude_once_adj_candidate"
    if next_token in PRONOUNS:
        return "keep_once_pronoun_clause"
    if next_token in DEMONSTRATIVES:
        return "keep_once_demonstrative_clause"
    if next_token in DETERMINERS:
        return "keep_once_determiner_clause"
    return "review"


def build_audit(df):
    supported_once = df[
        (df["is_priming_supported"] == 1)
        & (df["detected_item"].astype(str).str.lower().str.strip() == "once")
    ].copy()

    if supported_once.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    contexts = supported_once.apply(context_fields, axis=1, result_type="expand")
    supported_once["left_context"] = contexts[0]
    supported_once["right_context"] = contexts[1]
    supported_once["previous_token"] = contexts[2]
    supported_once["next_token"] = contexts[3]
    supported_once["following_3_tokens"] = contexts[4]
    supported_once["suggested_pattern"] = supported_once.apply(
        lambda row: suggest_pattern(row["next_token"], row["right_context"]),
        axis=1,
    )
    supported_once["manual_label"] = ""
    supported_once["notes"] = ""

    for column in OUTPUT_COLUMNS:
        if column not in supported_once.columns:
            supported_once[column] = ""

    return supported_once[OUTPUT_COLUMNS].sort_values(
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
    print("Supported once cases:", len(audit))
    print("\nCounts by suggested_pattern:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["suggested_pattern"].value_counts().to_string())

    print("\nFirst 20 rows:")
    preview_cols = ["corpus", "text_id", "suggested_pattern", "next_token", "sentence"]
    print(audit[preview_cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
