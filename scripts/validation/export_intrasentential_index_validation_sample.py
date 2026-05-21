from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

CASES_FILE = BASE_DIR / "outputs" / "intrasentential_outputs" / "04_cases_evidence.csv"
OUT_DIR = BASE_DIR / "outputs" / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "intrasentential_index_validation_sample.xlsx"

RANDOM_SEED = 42
TEXTS_PER_CORPUS = 50
CASES_PER_CORPUS = 100
RISKY_CASES_TOTAL = 150

RISKY_ITEMS = {
    "and", "but", "so", "as", "when", "then", "while", "since", "or"
}

MANUAL_COLUMNS = {
    "manual_valid_intrasentential": "",
    "manual_clause_linking": "",
    "manual_taxis_correct": "",
    "manual_macro_correct": "",
    "manual_notes": "",
}


def add_manual_columns(df):
    df = df.copy()
    for col, default in MANUAL_COLUMNS.items():
        df[col] = default
    return df


def make_context_window(row):
    sentence = str(row.get("sentence", ""))
    item = str(row.get("detected_item", ""))

    if not item or not sentence:
        return sentence

    # Simple display marker; does not alter the original sentence column.
    return sentence.replace(item, f"[{item}]", 1)


def main():
    print("Loading intra-sentential cases...")
    cases = pd.read_csv(CASES_FILE, low_memory=False)

    print("Rows:", len(cases))
    print("Corpora:", cases["corpus"].value_counts().to_dict())

    # Ensure useful display columns.
    cases["detected_item_lower"] = cases["detected_item"].astype(str).str.lower().str.strip()
    cases["context_with_marker"] = cases.apply(make_context_window, axis=1)

    # ------------------------------------------------------------------
    # 1. Random-text-based sample
    # ------------------------------------------------------------------
    random_text_case_frames = []
    selected_text_rows = []

    for corpus, corpus_df in cases.groupby("corpus"):
        text_ids = (
            corpus_df[["corpus", "text_id", "group"]]
            .drop_duplicates()
            .sample(
                n=min(TEXTS_PER_CORPUS, corpus_df["text_id"].nunique()),
                random_state=RANDOM_SEED,
            )
        )

        selected_text_rows.append(text_ids)

        sampled_cases = corpus_df[
            corpus_df["text_id"].isin(text_ids["text_id"])
        ].copy()

        sampled_cases = sampled_cases.sample(
            n=min(CASES_PER_CORPUS, len(sampled_cases)),
            random_state=RANDOM_SEED,
        )

        random_text_case_frames.append(sampled_cases)

    random_text_cases = pd.concat(random_text_case_frames, ignore_index=True)
    selected_texts = pd.concat(selected_text_rows, ignore_index=True)

    random_text_cases["validation_sample_type"] = "random_text_cases"

    # ------------------------------------------------------------------
    # 2. Risky-item oversample
    # ------------------------------------------------------------------
    risky = cases[cases["detected_item_lower"].isin(RISKY_ITEMS)].copy()

    # Avoid duplicating cases already in random sample where possible.
    random_keys = set(
        zip(
            random_text_cases["corpus"],
            random_text_cases["text_id"],
            random_text_cases["sentence_index"],
            random_text_cases["detected_item"],
            random_text_cases["connector_start_char"],
            random_text_cases["connector_end_char"],
        )
    )

    risky["case_key"] = list(
        zip(
            risky["corpus"],
            risky["text_id"],
            risky["sentence_index"],
            risky["detected_item"],
            risky["connector_start_char"],
            risky["connector_end_char"],
        )
    )

    risky = risky[~risky["case_key"].isin(random_keys)].copy()

    # Stratify roughly across risky items.
    risky_frames = []
    per_item = max(1, RISKY_CASES_TOTAL // len(RISKY_ITEMS))

    for item, item_df in risky.groupby("detected_item_lower"):
        risky_frames.append(
            item_df.sample(
                n=min(per_item, len(item_df)),
                random_state=RANDOM_SEED,
            )
        )

    risky_cases = pd.concat(risky_frames, ignore_index=True)

    # If slightly under target, top up randomly.
    if len(risky_cases) < RISKY_CASES_TOTAL:
        used_keys = set(risky_cases["case_key"])
        remaining = risky[~risky["case_key"].isin(used_keys)]
        top_up = remaining.sample(
            n=min(RISKY_CASES_TOTAL - len(risky_cases), len(remaining)),
            random_state=RANDOM_SEED,
        )
        risky_cases = pd.concat([risky_cases, top_up], ignore_index=True)

    risky_cases = risky_cases.drop(columns=["case_key"], errors="ignore")
    risky_cases["validation_sample_type"] = "risky_item_cases"

    # ------------------------------------------------------------------
    # 3. Add manual columns and organise columns
    # ------------------------------------------------------------------
    useful_cols = [
        "validation_sample_type",
        "corpus",
        "text_id",
        "group",
        "sentence_index",
        "detected_item",
        "detected_item_lower",
        "sentence",
        "context_with_marker",
        "macro_category",
        "path_2",
        "path_3",
        "path_4",
        "path_5",
        "taxis",
        "is_problematic_multifunctional",
        "priming_decision",
        "priming_confidence",
        "priming_notes",
        "is_priming_supported",
        "word_count_text",
        "sentence_count_text",
        "source_file",
        "algorithm_notes",
    ]

    useful_cols = [c for c in useful_cols if c in cases.columns]

    random_text_cases = add_manual_columns(random_text_cases[useful_cols])
    risky_cases = add_manual_columns(risky_cases[useful_cols])

    combined = pd.concat([random_text_cases, risky_cases], ignore_index=True)

    selected_texts = selected_texts.sort_values(["corpus", "text_id"])

    instructions = pd.DataFrame([
        {
            "Field": "manual_valid_intrasentential",
            "Guidance": "Mark yes/no/uncertain. Does the detected item function as an intra-sentential conjunction in this sentence?",
        },
        {
            "Field": "manual_clause_linking",
            "Guidance": "Mark yes/no/uncertain. Does the item link clauses or clause-like units rather than only words/phrases?",
        },
        {
            "Field": "manual_taxis_correct",
            "Guidance": "Mark yes/no/uncertain. Is the paratactic/hypotactic assignment acceptable?",
        },
        {
            "Field": "manual_macro_correct",
            "Guidance": "Mark yes/no/uncertain. Is the macro category Extension/Elaboration/Enhancement acceptable?",
        },
        {
            "Field": "manual_notes",
            "Guidance": "Add short comments, especially for false positives, ambiguity, learner grammar, or phrase-level coordination.",
        },
        {
            "Field": "Suggested validation interpretation",
            "Guidance": "Broad sample estimates overall precision. Risky-item sample estimates behaviour of multifunctional/high-risk connectors.",
        },
    ])

    summary = pd.DataFrame([
        {
            "sample_component": "random_text_cases",
            "rows": len(random_text_cases),
            "design": f"{TEXTS_PER_CORPUS} random texts per corpus; up to {CASES_PER_CORPUS} detected cases per corpus",
        },
        {
            "sample_component": "risky_item_cases",
            "rows": len(risky_cases),
            "design": f"Risky connector oversample from {sorted(RISKY_ITEMS)}",
        },
        {
            "sample_component": "combined",
            "rows": len(combined),
            "design": "Random-text cases plus risky-item oversample",
        },
    ])

    with pd.ExcelWriter(OUT_FILE, engine="openpyxl") as writer:
        instructions.to_excel(writer, sheet_name="Instructions", index=False)
        summary.to_excel(writer, sheet_name="Sample summary", index=False)
        selected_texts.to_excel(writer, sheet_name="Selected texts", index=False)
        random_text_cases.to_excel(writer, sheet_name="Random text cases", index=False)
        risky_cases.to_excel(writer, sheet_name="Risky item cases", index=False)
        combined.to_excel(writer, sheet_name="Combined sample", index=False)

        for sheet in writer.sheets.values():
            sheet.freeze_panes = "A2"

    print("Wrote:", OUT_FILE)
    print("\nSummary:")
    print(summary.to_string(index=False))

    print("\nRandom-text sample by corpus:")
    print(
        random_text_cases.groupby("corpus")
        .size()
        .reset_index(name="n_cases")
        .to_string(index=False)
    )

    print("\nRisky sample by item:")
    print(
        risky_cases["detected_item_lower"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "detected_item", "detected_item_lower": "n"})
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()