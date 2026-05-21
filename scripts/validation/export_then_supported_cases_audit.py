from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_FILE = OUT_DIR / "then_supported_cases_audit.csv"

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

VERB_LIKE_STARTERS = {
    "go",
    "goes",
    "went",
    "come",
    "comes",
    "came",
    "take",
    "takes",
    "took",
    "put",
    "puts",
    "open",
    "opens",
    "opened",
    "leave",
    "leaves",
    "left",
    "decide",
    "decides",
    "decided",
    "start",
    "starts",
    "started",
    "finish",
    "finishes",
    "finished",
    "submit",
    "submits",
    "submitted",
    "buy",
    "buys",
    "bought",
    "try",
    "tries",
    "tried",
}


def as_int(value):
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def find_then_span(row):
    sentence = str(row.get("sentence", ""))
    start = as_int(row.get("connector_start_char"))
    end = as_int(row.get("connector_end_char"))

    if start is not None and end is not None:
        if 0 <= start < end <= len(sentence):
            if sentence[start:end].lower() == "then":
                return start, end

    match = re.search(r"\bthen\b", sentence, flags=re.IGNORECASE)
    if match:
        return match.start(), match.end()

    return None, None


def tokenize(text):
    return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?", str(text).lower())


def context_fields(row):
    sentence = str(row.get("sentence", ""))
    start, end = find_then_span(row)

    if start is None or end is None:
        return "", "", "", ""

    left_context = sentence[max(0, start - 120):start]
    right_context = sentence[end:end + 120]
    previous_tokens = tokenize(left_context)
    following_tokens = tokenize(right_context)

    previous_token = previous_tokens[-1] if previous_tokens else ""
    next_token = following_tokens[0] if following_tokens else ""
    following_3_tokens = " ".join(following_tokens[:3])
    left_tokens = " ".join(previous_tokens[-12:])

    return previous_token, next_token, following_3_tokens, left_tokens


def suggest_pattern(row):
    previous_token = str(row["previous_token"]).lower().strip()
    next_token = str(row["next_token"]).lower().strip()
    following_3_tokens = str(row["following_3_tokens"]).lower().strip()
    left_tokens = str(row["_left_tokens"]).lower().strip()

    if re.search(r"\bif\b", left_tokens):
        return "keep_if_then_consequence"

    if previous_token in {"since", "by", "until"}:
        return "review_then_temporal_adjunct"
    if previous_token == "from" or following_3_tokens.startswith("on"):
        if previous_token == "from" or re.search(r"\bfrom\s+then\s+on\b", left_tokens + " then " + following_3_tokens):
            return "review_then_temporal_adjunct"

    if re.search(r"\bnow\s+and\s+then\b", left_tokens + " then"):
        return "review_then_idiom_frequency"
    if re.search(r"\bevery\s+now\s+and\s+then\b", left_tokens + " then"):
        return "review_then_idiom_frequency"

    if (
        next_token in PRONOUNS
        or next_token in DETERMINERS
        or next_token in COMMON_NOUNS
        or next_token in VERB_LIKE_STARTERS
    ):
        return "keep_then_sequence_clause"

    if re.match(r"^[a-z]+ (am|is|are|was|were|can|could|will|would|should|must|has|have|had|do|does|did)\b", following_3_tokens):
        return "keep_then_sequence_clause"

    return "review"


def build_audit(df):
    supported_then = df[
        (df["is_priming_supported"] == 1)
        & (df["detected_item"].astype(str).str.lower().str.strip() == "then")
    ].copy()

    if supported_then.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    contexts = supported_then.apply(context_fields, axis=1, result_type="expand")
    supported_then["previous_token"] = contexts[0]
    supported_then["next_token"] = contexts[1]
    supported_then["following_3_tokens"] = contexts[2]
    supported_then["_left_tokens"] = contexts[3]
    supported_then["suggested_pattern"] = supported_then.apply(suggest_pattern, axis=1)
    supported_then["manual_label"] = ""
    supported_then["notes"] = ""

    for column in OUTPUT_COLUMNS:
        if column not in supported_then.columns:
            supported_then[column] = ""

    return supported_then[OUTPUT_COLUMNS].sort_values(
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
    print("Supported then cases:", len(audit))

    print("\nCounts by suggested_pattern:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["suggested_pattern"].value_counts().to_string())

    print("\nTop 40 previous_token counts:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["previous_token"].fillna("").value_counts().head(40).to_string())

    print("\nTop 40 next_token counts:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["next_token"].fillna("").value_counts().head(40).to_string())

    preview_cols = [
        "corpus",
        "text_id",
        "suggested_pattern",
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
