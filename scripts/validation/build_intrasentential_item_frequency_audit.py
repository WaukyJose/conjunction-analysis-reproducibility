from pathlib import Path
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "scripts"))

from output_utils.scalable_indices import build_feature_code


INPUT_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_FILE = OUT_DIR / "intrasentential_item_frequency_audit.csv"

AMBIGUOUS_ITEMS = {
    "rather",
    "as",
    "while",
    "since",
    "so",
    "then",
    "still",
    "once",
    "where",
    "when",
    "and",
    "or",
    "but",
}

OUTPUT_COLUMNS = [
    "corpus",
    "detected_item",
    "feature_code",
    "macro_category",
    "path_2",
    "path_3",
    "path_4",
    "path_5",
    "taxis",
    "n_cases",
    "n_texts",
    "mean_per_1000",
    "sample_sentence_1",
    "sample_sentence_2",
    "sample_sentence_3",
    "known_ambiguous_item",
    "suspicion_note",
]


def truncate_sentence(sentence, max_chars=250):
    sentence = str(sentence).strip()
    if len(sentence) <= max_chars:
        return sentence
    return sentence[:max_chars].rstrip()


def sample_sentences(group):
    if "sentence" not in group.columns:
        return ["", "", ""]
    unique_sentences = []
    seen = set()
    for sentence in group["sentence"].dropna().astype(str):
        sentence = sentence.strip()
        if not sentence or sentence in seen:
            continue
        seen.add(sentence)
        unique_sentences.append(truncate_sentence(sentence))
        if len(unique_sentences) == 3:
            break
    return unique_sentences + [""] * (3 - len(unique_sentences))


def build_audit(df):
    supported = df[df["is_priming_supported"] == 1].copy()
    supported["feature_code"] = supported.apply(
        lambda row: build_feature_code(row, prefix="intra"),
        axis=1,
    )

    if "word_count_text" in supported.columns:
        word_count = pd.to_numeric(supported["word_count_text"], errors="coerce")
        supported["case_per_1000"] = (1 / word_count * 1000).where(word_count > 0, 0)
    else:
        supported["case_per_1000"] = 0

    rows = []
    group_cols = ["corpus", "detected_item", "feature_code"]
    for (corpus, detected_item, feature_code), group in supported.groupby(group_cols, dropna=False):
        first = group.iloc[0]
        ambiguous = int(str(detected_item).lower().strip() in AMBIGUOUS_ITEMS)
        samples = sample_sentences(group)
        rows.append({
            "corpus": corpus,
            "detected_item": detected_item,
            "feature_code": feature_code,
            "macro_category": first.get("macro_category", ""),
            "path_2": first.get("path_2", ""),
            "path_3": first.get("path_3", ""),
            "path_4": first.get("path_4", ""),
            "path_5": first.get("path_5", ""),
            "taxis": first.get("taxis", ""),
            "n_cases": len(group),
            "n_texts": group["text_id"].nunique() if "text_id" in group.columns else 0,
            "mean_per_1000": group["case_per_1000"].mean(),
            "sample_sentence_1": samples[0],
            "sample_sentence_2": samples[1],
            "sample_sentence_3": samples[2],
            "known_ambiguous_item": ambiguous,
            "suspicion_note": (
                "Known multifunctional item; inspect samples."
                if ambiguous
                else ""
            ),
        })

    audit = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    if not audit.empty:
        audit = audit.sort_values(
            ["corpus", "n_cases", "detected_item"],
            ascending=[True, False, True],
        )
    return supported, audit


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    if "is_priming_supported" not in df.columns:
        raise ValueError("Missing required column: is_priming_supported")

    supported, audit = build_audit(df)
    audit.to_csv(OUT_FILE, index=False)

    print("Input path:", INPUT_FILE)
    print("Output path:", OUT_FILE)
    print("Rows read:", len(df))
    print("Supported rows:", len(supported))
    print("Audit rows:", len(audit))
    print("\nTop 20 rows by n_cases:")
    print(
        audit.sort_values("n_cases", ascending=False)
        .head(20)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
