from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_FILE = OUT_DIR / "as_supported_cases_audit.csv"

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
    "story",
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
    "being",
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
    "begin",
    "begins",
    "began",
    "start",
    "starts",
    "started",
    "leave",
    "leaves",
    "leaving",
    "arrive",
    "arrives",
    "arrived",
}

ADJECTIVE_ADVERB_WORDS = {
    "bad",
    "beautiful",
    "big",
    "busy",
    "clear",
    "common",
    "difficult",
    "easy",
    "far",
    "fast",
    "good",
    "great",
    "happy",
    "hard",
    "high",
    "important",
    "interesting",
    "long",
    "low",
    "much",
    "quickly",
    "short",
    "slowly",
    "strong",
    "well",
}


def as_int(value):
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def find_as_span(row):
    sentence = str(row.get("sentence", ""))
    start = as_int(row.get("connector_start_char"))
    end = as_int(row.get("connector_end_char"))

    if start is not None and end is not None:
        if 0 <= start < end <= len(sentence):
            if sentence[start:end].lower() == "as":
                return start, end

    match = re.search(r"\bas\b", sentence, flags=re.IGNORECASE)
    if match:
        return match.start(), match.end()

    return None, None


def tokenize(text):
    return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?", str(text).lower())


def context_fields(row):
    sentence = str(row.get("sentence", ""))
    start, end = find_as_span(row)

    if start is None or end is None:
        return "", "", "", ""

    left_context = sentence[max(0, start - 80):start]
    right_context = sentence[end:end + 120]
    previous_tokens = tokenize(left_context)
    following_tokens = tokenize(right_context)

    previous_token = previous_tokens[-1] if previous_tokens else ""
    next_token = following_tokens[0] if following_tokens else ""
    following_3_tokens = " ".join(following_tokens[:3])
    local_tokens = " ".join(previous_tokens[-4:] + ["as"] + following_tokens[:6])

    return previous_token, next_token, following_3_tokens, local_tokens


def has_finite_verb_cue(tokens):
    return any(token in FINITE_VERB_CUES for token in tokens[:6])


def suggest_pattern(row):
    previous_token = str(row["previous_token"]).lower().strip()
    next_token = str(row["next_token"]).lower().strip()
    following_3_tokens = str(row["following_3_tokens"]).lower().strip()
    following_tokens = following_3_tokens.split()
    local_tokens = str(row["_local_tokens"]).lower().strip()

    if re.search(r"\bsuch\s+as\b", local_tokens):
        return "review_as_multiword_overlap"
    if re.search(r"\bas\s+well\s+as\b", local_tokens):
        return "review_as_multiword_overlap"
    if re.search(r"\bas\s+soon\s+as\b", local_tokens):
        return "review_as_multiword_overlap"
    if re.search(r"\bas\s+long\s+as\b", local_tokens):
        return "review_as_multiword_overlap"
    if re.search(r"\bas\s+a\s+result\b", local_tokens):
        return "review_as_multiword_overlap"

    if re.search(r"\bas\s+\w+\s+as\b", local_tokens):
        return "review_as_comparison"
    if next_token in ADJECTIVE_ADVERB_WORDS and re.search(r"\bas\s+" + re.escape(next_token) + r"\s+as\b", local_tokens):
        return "review_as_comparison"

    if re.search(r"\bas\s+part\s+of\b", local_tokens):
        return "review_as_prepositional_like"
    if re.search(r"\bas\s+one\s+of\b", local_tokens):
        return "review_as_prepositional_like"
    if re.search(r"\bas\s+much\s+as\b", local_tokens):
        return "review_as_prepositional_like"

    if next_token in {"a", "an"}:
        return "review_as_role_np"
    if next_token in DETERMINERS and not has_finite_verb_cue(following_tokens):
        return "review_as_role_np"

    if next_token in PRONOUNS:
        return "keep_as_clause_candidate"
    if next_token in DETERMINERS or next_token in COMMON_NOUNS:
        if has_finite_verb_cue(following_tokens):
            return "keep_as_clause_candidate"

    if previous_token in {"known", "used", "seen", "served", "worked", "works", "working"}:
        return "review_as_prepositional_like"

    return "review"


def build_audit(df):
    supported_as = df[
        (df["is_priming_supported"] == 1)
        & (df["detected_item"].astype(str).str.lower().str.strip() == "as")
    ].copy()

    if supported_as.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    contexts = supported_as.apply(context_fields, axis=1, result_type="expand")
    supported_as["previous_token"] = contexts[0]
    supported_as["next_token"] = contexts[1]
    supported_as["following_3_tokens"] = contexts[2]
    supported_as["_local_tokens"] = contexts[3]
    supported_as["suggested_pattern"] = supported_as.apply(suggest_pattern, axis=1)
    supported_as["manual_label"] = ""
    supported_as["notes"] = ""

    for column in OUTPUT_COLUMNS:
        if column not in supported_as.columns:
            supported_as[column] = ""

    return supported_as[OUTPUT_COLUMNS].sort_values(
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
    print("Supported as cases:", len(audit))

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

    print("\nFirst 120 review/multiword candidates:")
    review_rows = audit[
        audit["suggested_pattern"].astype(str).str.startswith("review")
    ]
    if review_rows.empty:
        print("(none)")
    else:
        print(review_rows[preview_cols].head(120).to_string(index=False))


if __name__ == "__main__":
    main()
