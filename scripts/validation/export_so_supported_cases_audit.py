from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_FILE = OUT_DIR / "so_supported_cases_audit.csv"

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

MODALS_AUXILIARIES = {
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
}

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
    "school",
    "system",
    "team",
    "result",
    "problem",
    "person",
    "man",
    "woman",
}

QUANTIFIERS = {"much", "many", "little", "few"}

ADJECTIVE_ADVERB_WORDS = {
    "bad",
    "beautiful",
    "big",
    "busy",
    "clear",
    "close",
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
    "many",
    "much",
    "nice",
    "old",
    "quick",
    "quickly",
    "sad",
    "serious",
    "short",
    "small",
    "strong",
    "sure",
    "well",
}

ADJECTIVE_ADVERB_SUFFIXES = (
    "able",
    "al",
    "ant",
    "ary",
    "ent",
    "ful",
    "ible",
    "ic",
    "ing",
    "ive",
    "less",
    "ly",
    "ous",
)


def as_int(value):
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def find_so_span(row):
    sentence = str(row.get("sentence", ""))
    start = as_int(row.get("connector_start_char"))
    end = as_int(row.get("connector_end_char"))

    if start is not None and end is not None:
        if 0 <= start < end <= len(sentence):
            if sentence[start:end].lower() == "so":
                return start, end

    match = re.search(r"\bso\b", sentence, flags=re.IGNORECASE)
    if match:
        return match.start(), match.end()

    return None, None


def tokenize(text):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", str(text).lower())


def context_fields(row):
    sentence = str(row.get("sentence", ""))
    start, end = find_so_span(row)

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


def is_adjective_or_adverb_like(token):
    token = str(token).lower().strip()
    if token in ADJECTIVE_ADVERB_WORDS:
        return True
    if len(token) >= 5 and token.endswith(ADJECTIVE_ADVERB_SUFFIXES):
        return True
    return False


def suggest_pattern(row):
    left_context = str(row["left_context"]).lower()
    right_context = str(row["right_context"]).lower()
    previous_token = str(row["previous_token"]).lower().strip()
    next_token = str(row["next_token"]).lower().strip()
    following_3_tokens = str(row["following_3_tokens"]).lower().strip()
    left_local = left_context[-40:]

    if re.match(r"\s*-\s*called\b", right_context):
        return "exclude_so_idiom_candidate"
    if previous_token == "and" and following_3_tokens.startswith("on"):
        return "exclude_so_idiom_candidate"
    if next_token == "on":
        return "exclude_so_idiom_candidate"
    if next_token in {"far", "long", "what"}:
        return "exclude_so_idiom_candidate"
    if re.search(r"\bdo\s+you\s+think\s+so\s*$", left_local + "so"):
        if next_token:
            return "review_so_learner_complement_candidate"
        return "exclude_so_idiom_candidate"
    if re.search(r"\b(?:think|hope|believe)\s+so\s*$", left_local + "so"):
        if next_token:
            return "review_so_learner_complement_candidate"
        return "exclude_so_idiom_candidate"

    if next_token == "that":
        return "review_so_that_overlap"

    if next_token in QUANTIFIERS:
        return "exclude_so_quantifier_candidate"

    if (
        next_token in PRONOUNS
        or next_token in DETERMINERS
        or next_token in MODALS_AUXILIARIES
        or next_token in COMMON_NOUN_CLAUSE_STARTERS
        or re.match(r"^i['’][a-z]+$", next_token)
    ):
        return "keep_so_result_clause"

    if re.match(r"^[a-z]+ (can|could|will|would|should|must|is|are|was|were|has|have|had|do|does|did)\b", following_3_tokens):
        return "keep_so_result_clause"

    if is_adjective_or_adverb_like(next_token):
        return "exclude_so_intensifier_candidate"

    return "review"


def build_audit(df):
    supported_so = df[
        (df["is_priming_supported"] == 1)
        & (df["detected_item"].astype(str).str.lower().str.strip() == "so")
    ].copy()

    if supported_so.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    contexts = supported_so.apply(context_fields, axis=1, result_type="expand")
    supported_so["left_context"] = contexts[0]
    supported_so["right_context"] = contexts[1]
    supported_so["previous_token"] = contexts[2]
    supported_so["next_token"] = contexts[3]
    supported_so["following_3_tokens"] = contexts[4]
    supported_so["suggested_pattern"] = supported_so.apply(suggest_pattern, axis=1)
    supported_so["manual_label"] = ""
    supported_so["notes"] = ""

    for column in OUTPUT_COLUMNS:
        if column not in supported_so.columns:
            supported_so[column] = ""

    return supported_so[OUTPUT_COLUMNS].sort_values(
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
    print("Supported so cases:", len(audit))

    print("\nCounts by suggested_pattern:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["suggested_pattern"].value_counts().to_string())

    print("\nTop 50 next_token counts:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["next_token"].fillna("").value_counts().head(50).to_string())

    print("\nTop 50 following_3_tokens counts:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["following_3_tokens"].fillna("").value_counts().head(50).to_string())

    preview_cols = [
        "corpus",
        "text_id",
        "suggested_pattern",
        "previous_token",
        "next_token",
        "following_3_tokens",
        "sentence",
    ]

    print("\nFirst 30 rows:")
    print(audit[preview_cols].head(30).to_string(index=False))

    print("\nFirst 100 likely exclusion candidates:")
    exclusion_patterns = {
        "exclude_so_quantifier_candidate",
        "exclude_so_intensifier_candidate",
        "exclude_so_idiom_candidate",
    }
    exclusions = audit[audit["suggested_pattern"].isin(exclusion_patterns)]
    if exclusions.empty:
        print("(none)")
    else:
        print(exclusions[preview_cols].head(100).to_string(index=False))


if __name__ == "__main__":
    main()
