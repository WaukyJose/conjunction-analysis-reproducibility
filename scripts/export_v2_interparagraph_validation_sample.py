from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
IN_FILE = BASE_DIR / "outputs" / "v2_interparagraph_sample" / "v2_interparagraph_gig_sample_cases.csv"
OUT_DIR = BASE_DIR / "validation" / "v2_interparagraph"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "v2_interparagraph_gig_validation_sample_N30.csv"

N_CASES = 30
RANDOM_SEED = 123


def main():
    df = pd.read_csv(IN_FILE, low_memory=False)

    n = min(N_CASES, len(df))
    out = df.sample(n=n, random_state=RANDOM_SEED).copy()

    out["manual_detection_correct"] = ""
    out["manual_position_correct"] = ""
    out["manual_category_correct"] = ""
    out["manual_error_type"] = ""
    out["manual_notes"] = ""

    keep_cols = [
        "corpus",
        "text_id",
        "group",
        "paragraph_index",
        "previous_paragraph",
        "current_paragraph",
        "detected_item",
        "macro_category",
        "path_2",
        "path_3",
        "path_4",
        "path_5",
        "paragraph_start_cleaned",
        "word_count_text",
        "paragraph_count_text",
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
    print(out["detected_item"].str.lower().value_counts().head(20).to_string())


if __name__ == "__main__":
    main()