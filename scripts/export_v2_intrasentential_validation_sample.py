from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
IN_FILE = BASE_DIR / "outputs" / "v2_intrasentential_sample" / "v2_intrasentential_sample_cases.csv"
OUT_DIR = BASE_DIR / "validation" / "v2_intrasentential"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "v2_intrasentential_validation_sample_N10_per_corpus.csv"

N_PER_CORPUS = 10
RANDOM_SEED = 123


def make_context(row, window=120):
    sentence = str(row.get("sentence", ""))
    start = int(row.get("connector_start_char", 0))
    end = int(row.get("connector_end_char", 0))

    left = sentence[max(0, start - window):start]
    hit = sentence[start:end]
    right = sentence[end:end + window]

    return left + "[" + hit + "]" + right


def main():
    df = pd.read_csv(IN_FILE)

    samples = []

    for corpus, sub in df.groupby("corpus"):
        n = min(N_PER_CORPUS, len(sub))
        sample = sub.sample(n=n, random_state=RANDOM_SEED).copy()
        samples.append(sample)

    out = pd.concat(samples, ignore_index=True)

    out["validation_context"] = out.apply(make_context, axis=1)

    out["manual_detection_correct"] = ""
    out["manual_position_correct"] = ""
    out["manual_category_correct"] = ""
    out["manual_taxis_correct"] = ""
    out["manual_error_type"] = ""
    out["manual_notes"] = ""

    keep_cols = [
        "corpus",
        "text_id",
        "group",
        "sentence_index",
        "sentence",
        "validation_context",
        "detected_item",
        "macro_category",
        "taxis",
        "path_2",
        "path_3",
        "path_4",
        "path_5",
        "connector_start_char",
        "connector_end_char",
        "word_count_text",
        "source_file",
        "algorithm_notes",
        "manual_detection_correct",
        "manual_position_correct",
        "manual_category_correct",
        "manual_taxis_correct",
        "manual_error_type",
        "manual_notes",
    ]

    out = out[[c for c in keep_cols if c in out.columns]]
    out.to_csv(OUT_FILE, index=False)

    print("Wrote:", OUT_FILE)
    print("Rows:", len(out))
    print(out["corpus"].value_counts().to_string())


if __name__ == "__main__":
    main()