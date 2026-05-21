from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
IN_FILE = BASE_DIR / "outputs" / "v2_intersentential_sample" / "v2_intersentential_sample_cases.csv"
OUT_DIR = BASE_DIR / "validation" / "v2_intersentential"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "v2_intersentential_validation_sample_N30_per_corpus.csv"

N_PER_CORPUS = 30
RANDOM_SEED = 123


def main():
    df = pd.read_csv(IN_FILE)

    samples = []

    for corpus, sub in df.groupby("corpus"):
        n = min(N_PER_CORPUS, len(sub))
        sample = sub.sample(n=n, random_state=RANDOM_SEED).copy()
        samples.append(sample)

    out = pd.concat(samples, ignore_index=True)

    # Manual annotation columns
    out["manual_detection_correct"] = ""
    out["manual_position_correct"] = ""
    out["manual_category_correct"] = ""
    out["manual_error_type"] = ""
    out["manual_notes"] = ""

    keep_cols = [
        "corpus",
        "text_id",
        "group",
        "sentence_index",
        "previous_sentence",
        "current_sentence",
        "detected_item",
        "macro_category",
        "path_2",
        "path_3",
        "path_4",
        "path_5",
        "sentence_start_cleaned",
        "word_count_text",
        "source_file",
        "algorithm_notes",
        "manual_detection_correct",
        "manual_position_correct",
        "manual_category_correct",
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