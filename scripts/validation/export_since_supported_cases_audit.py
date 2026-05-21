from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_FILE = OUT_DIR / "since_supported_cases_audit.csv"

OUTPUT_COLUMNS = [
    "corpus",
    "text_id",
    "detected_item",
    "macro_category",
    "path_2",
    "path_3",
    "path_4",
    "taxis",
    "priming_decision",
    "priming_confidence",
    "priming_reason",
    "sentence",
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
    "there",
}

DETERMINERS = {
    "a",
    "an",
    "the",
    "this",
    "that",
    "these",
    "those",
    "my",
    "your",
    "his",
    "her",
    "its",
    "our",
    "their",
    "some",
    "many",
    "most",
    "all",
}

COMMON_NOUNS = {
    "people",
    "students",
    "children",
    "parents",
    "teachers",
    "workers",
    "companies",
    "government",
    "society",
    "school",
    "system",
    "team",
    "problem",
    "result",
    "person",
    "man",
    "woman",
}

FINITE_VERB_CUES = {
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "do",
    "does",
    "did",
    "have",
    "has",
    "had",
    "can",
    "could",
    "will",
    "would",
    "shall",
    "should",
    "may",
    "might",
    "must",
    "need",
    "needs",
    "needed",
    "arrived",
    "started",
    "began",
    "came",
    "went",
    "got",
    "became",
    "finished",
    "happened",
}

MONTHS = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}

TIME_WORDS = {
    "yesterday",
    "today",
    "childhood",
    "morning",
    "afternoon",
    "evening",
    "night",
}

RELATIVE_TIME_STARTERS = {"last", "this", "that", "next"}


def as_int(value):
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def find_since_span(row):
    sentence = str(row.get("sentence", ""))
    start = as_int(row.get("connector_start_char"))
    end = as_int(row.get("connector_end_char"))

    if start is not None and end is not None:
        if 0 <= start < end <= len(sentence):
            if sentence[start:end].lower() == "since":
                return start, end

    match = re.search(r"\bsince\b", sentence, flags=re.IGNORECASE)
    if match:
        return match.start(), match.end()

    return None, None


def tokenize(text):
    return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?", str(text).lower())


def context_fields(row):
    sentence = str(row.get("sentence", ""))
    start, end = find_since_span(row)

    if start is None or end is None:
        return "", "", ""

    left_context = sentence[max(0, start - 80):start]
    right_context = sentence[end:end + 120]
    previous_tokens = tokenize(left_context)
    following_tokens = tokenize(right_context)

    previous_token = previous_tokens[-1] if previous_tokens else ""
    next_token = following_tokens[0] if following_tokens else ""
    following_3_tokens = " ".join(following_tokens[:3])

    return previous_token, next_token, following_3_tokens


def has_finite_verb_cue(tokens):
    return any(token in FINITE_VERB_CUES for token in tokens[:5])


def is_temporal_adjunct(next_token, following_tokens):
    if re.fullmatch(r"\d{2,4}", next_token):
        return True
    if next_token in MONTHS or next_token in TIME_WORDS:
        return True
    if next_token in RELATIVE_TIME_STARTERS and len(following_tokens) >= 2:
        if following_tokens[1] in {"day", "week", "month", "year", "time", "night", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}:
            return True
    return False


def suggest_pattern(row):
    next_token = str(row["next_token"]).lower().strip()
    following_3_tokens = str(row["following_3_tokens"]).lower().strip()
    following_tokens = following_3_tokens.split()

    if next_token == "then" or following_3_tokens.startswith("then"):
        return "review_since_then_ever_since"

    if str(row["previous_token"]).lower().strip() == "ever":
        return "review_since_then_ever_since"

    if is_temporal_adjunct(next_token, following_tokens):
        return "review_since_temporal_adjunct"

    if next_token in PRONOUNS:
        if has_finite_verb_cue(following_tokens):
            return "keep_since_causal_clause_candidate"
        return "keep_since_clause_candidate"

    if next_token in DETERMINERS or next_token in COMMON_NOUNS:
        if has_finite_verb_cue(following_tokens):
            return "keep_since_clause_candidate"
        return "review"

    return "review"


def build_audit(df):
    supported_since = df[
        (df["is_priming_supported"] == 1)
        & (df["detected_item"].astype(str).str.lower().str.strip() == "since")
    ].copy()

    if supported_since.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    contexts = supported_since.apply(context_fields, axis=1, result_type="expand")
    supported_since["previous_token"] = contexts[0]
    supported_since["next_token"] = contexts[1]
    supported_since["following_3_tokens"] = contexts[2]
    supported_since["suggested_pattern"] = supported_since.apply(suggest_pattern, axis=1)
    supported_since["manual_label"] = ""
    supported_since["notes"] = ""

    for column in OUTPUT_COLUMNS:
        if column not in supported_since.columns:
            supported_since[column] = ""

    return supported_since[OUTPUT_COLUMNS].sort_values(
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
    print("Supported since cases:", len(audit))

    print("\nCounts by suggested_pattern:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["suggested_pattern"].value_counts().to_string())

    print("\nCounts by priming_decision:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["priming_decision"].fillna("").value_counts().to_string())

    print("\nTop 40 next_token counts:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["next_token"].fillna("").value_counts().head(40).to_string())

    preview_cols = [
        "corpus",
        "text_id",
        "suggested_pattern",
        "priming_decision",
        "previous_token",
        "next_token",
        "following_3_tokens",
        "sentence",
    ]

    print("\nFirst 50 rows:")
    print(audit[preview_cols].head(50).to_string(index=False))

    print("\nFirst 100 review candidates:")
    review_rows = audit[audit["suggested_pattern"].astype(str).str.startswith("review")]
    if review_rows.empty:
        print("(none)")
    else:
        print(review_rows[preview_cols].head(100).to_string(index=False))


if __name__ == "__main__":
    main()
