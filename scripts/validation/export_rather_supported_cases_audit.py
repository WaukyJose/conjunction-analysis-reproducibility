from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_FILE = OUT_DIR / "rather_supported_cases_audit.csv"

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
    "suggested_pattern",
    "manual_label",
    "notes",
]


def as_int(value):
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def find_rather_span(row):
    sentence = str(row.get("sentence", ""))
    start = as_int(row.get("connector_start_char"))
    end = as_int(row.get("connector_end_char"))

    if start is not None and end is not None:
        if 0 <= start < end <= len(sentence):
            if sentence[start:end].lower() == "rather":
                return start, end

    match = re.search(r"\brather\b", sentence, flags=re.IGNORECASE)
    if match:
        return match.start(), match.end()

    return None, None


def context_fields(row):
    sentence = str(row.get("sentence", ""))
    start, end = find_rather_span(row)

    if start is None or end is None:
        return "", "", sentence.lower()

    left_context = sentence[max(0, start - 80):start]
    right_context = sentence[end:end + 120]
    local_context = sentence[max(0, start - 40):end + 80].lower()
    return left_context, right_context, local_context


def suggest_pattern(local_context):
    if re.search(r"\brather\s+than\b", local_context):
        return "keep_rather_than"
    if re.search(r"\bor\s+rather\b", local_context):
        return "keep_or_rather"
    if re.search(r"\bbut\s+rather\b", local_context):
        return "keep_but_rather"
    if re.search(r"\brather\s+(?!than\b)[a-z][a-z'-]*\b", local_context):
        return "possible_intensifier"
    return "review"


def build_audit(df):
    supported_rather = df[
        (df["is_priming_supported"] == 1)
        & (df["detected_item"].astype(str).str.lower().str.strip() == "rather")
    ].copy()

    if supported_rather.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    contexts = supported_rather.apply(context_fields, axis=1, result_type="expand")
    supported_rather["left_context"] = contexts[0]
    supported_rather["right_context"] = contexts[1]
    supported_rather["suggested_pattern"] = contexts[2].apply(suggest_pattern)
    supported_rather["manual_label"] = ""
    supported_rather["notes"] = ""

    for column in OUTPUT_COLUMNS:
        if column not in supported_rather.columns:
            supported_rather[column] = ""

    audit = supported_rather[OUTPUT_COLUMNS].sort_values(
        ["corpus", "text_id"],
        ascending=[True, True],
        kind="mergesort",
    )
    return audit


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
    print("Supported rather cases:", len(audit))
    print("\nCounts by suggested_pattern:")
    if audit.empty:
        print("(none)")
    else:
        print(audit["suggested_pattern"].value_counts().to_string())

    print("\nFirst 20 rows:")
    preview_cols = ["corpus", "text_id", "suggested_pattern", "sentence"]
    print(audit[preview_cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
