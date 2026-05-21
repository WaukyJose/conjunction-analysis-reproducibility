from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "outputs" / "v2_intrasentential_full"
OUT_DIR = BASE_DIR / "outputs" / "intrasentential_outputs"
VAL_DIR = BASE_DIR / "outputs" / "validation"
VAL_DIR.mkdir(parents=True, exist_ok=True)

CASES_FILE = RAW_DIR / "v2_intrasentential_full_cases.csv"
DIAG_FILE = OUT_DIR / "01_diagnostics.xlsx"
MACRO_FILE = OUT_DIR / "02_macro_taxis_indices.xlsx"
SUBCAT_FILE = OUT_DIR / "03_subcategory_indices.xlsx"
EVIDENCE_FILE = OUT_DIR / "04_cases_evidence.csv"

REPORT_FILE = VAL_DIR / "intrasentential_outcome_validation_report.xlsx"


def close_enough(a, b, tol=1e-8):
    return np.isclose(a, b, atol=tol, rtol=tol, equal_nan=True)


def main():
    print("Loading files...")

    cases = pd.read_csv(CASES_FILE, low_memory=False)
    diag = pd.read_excel(DIAG_FILE)
    macro = pd.read_excel(MACRO_FILE)
    subcat = pd.read_excel(SUBCAT_FILE)

    # Evidence file is huge; validate row count without loading full file.
    evidence_rows = sum(1 for _ in open(EVIDENCE_FILE, encoding="utf-8", errors="ignore")) - 1

    checks = []

    def add_check(name, passed, expected=None, observed=None, note=""):
        checks.append({
            "check": name,
            "passed": bool(passed),
            "expected": expected,
            "observed": observed,
            "note": note,
        })

    # ------------------------------------------------------------
    # 1. Basic row counts
    # ------------------------------------------------------------
    add_check(
        "Diagnostics row count equals macro row count",
        len(diag) == len(macro),
        len(diag),
        len(macro),
    )

    add_check(
        "Diagnostics row count equals subcategory row count",
        len(diag) == len(subcat),
        len(diag),
        len(subcat),
    )

    add_check(
        "Cases evidence CSV row count equals parser case rows",
        evidence_rows == len(cases),
        len(cases),
        evidence_rows,
    )

    # ------------------------------------------------------------
    # 2. Text ID alignment
    # ------------------------------------------------------------
    diag_ids = set(zip(diag["corpus"], diag["text_id"]))
    macro_ids = set(zip(macro["corpus"], macro["text_id"]))
    subcat_ids = set(zip(subcat["corpus"], subcat["text_id"]))
    case_ids = set(zip(cases["corpus"], cases["text_id"]))

    add_check(
        "Macro IDs equal diagnostics IDs",
        macro_ids == diag_ids,
        len(diag_ids),
        len(macro_ids),
    )

    add_check(
        "Subcategory IDs equal diagnostics IDs",
        subcat_ids == diag_ids,
        len(diag_ids),
        len(subcat_ids),
    )

    add_check(
        "Case IDs subset of diagnostics IDs",
        case_ids.issubset(diag_ids),
        "subset",
        case_ids.issubset(diag_ids),
    )

    # ------------------------------------------------------------
    # 3. Raw total counts from cases vs diagnostics/macro
    # ------------------------------------------------------------
    case_totals = (
        cases.groupby(["corpus", "text_id"])
        .size()
        .reset_index(name="case_intra_total_raw")
    )

    supported_totals = (
        cases[cases["is_priming_supported"] == 1]
        .groupby(["corpus", "text_id"])
        .size()
        .reset_index(name="case_supported_intra_total_raw")
    )

    merged = (
        macro[["corpus", "text_id", "word_count_text", "intra_total_raw", "supported_intra_total_raw"]]
        .merge(case_totals, on=["corpus", "text_id"], how="left")
        .merge(supported_totals, on=["corpus", "text_id"], how="left")
    )

    merged["case_intra_total_raw"] = merged["case_intra_total_raw"].fillna(0).astype(int)
    merged["case_supported_intra_total_raw"] = merged["case_supported_intra_total_raw"].fillna(0).astype(int)

    merged["broad_total_match"] = merged["intra_total_raw"] == merged["case_intra_total_raw"]
    merged["supported_total_match"] = (
        merged["supported_intra_total_raw"] == merged["case_supported_intra_total_raw"]
    )

    add_check(
        "Macro broad total raw equals case count by text",
        merged["broad_total_match"].all(),
        "all True",
        int((~merged["broad_total_match"]).sum()),
        "Observed = number of mismatching texts",
    )

    add_check(
        "Macro supported total raw equals supported case count by text",
        merged["supported_total_match"].all(),
        "all True",
        int((~merged["supported_total_match"]).sum()),
        "Observed = number of mismatching texts",
    )

    # ------------------------------------------------------------
    # 4. Per-1000 formula validation
    # ------------------------------------------------------------
    formula_checks = []

    rate_cols = [c for c in macro.columns if c.endswith("_per_1000")]
    raw_cols = [c.replace("_per_1000", "_raw") for c in rate_cols]

    for raw_col, rate_col in zip(raw_cols, rate_cols):
        if raw_col not in macro.columns:
            continue

        expected = (macro[raw_col] / macro["word_count_text"] * 1000).where(
            macro["word_count_text"] > 0
        )

        ok = close_enough(expected, macro[rate_col]).all()

        formula_checks.append({
            "raw_column": raw_col,
            "rate_column": rate_col,
            "passed": bool(ok),
            "max_abs_difference": float(np.nanmax(np.abs(expected - macro[rate_col]))),
        })

    formula_df = pd.DataFrame(formula_checks)

    add_check(
        "All macro per_1000 columns match raw / word_count * 1000",
        formula_df["passed"].all() if not formula_df.empty else False,
        "all True",
        formula_df.loc[~formula_df["passed"], "rate_column"].tolist()
        if not formula_df.empty else "no formula checks",
    )

    # ------------------------------------------------------------
    # 5. Make sure no wrong denominator columns exist
    # ------------------------------------------------------------
    bad_cols = [
        c for c in list(macro.columns) + list(subcat.columns)
        if "eligible_sentence_start" in c or "eligible_paragraph_start" in c
    ]

    add_check(
        "No eligible-start denominator columns in intra-sentential outputs",
        len(bad_cols) == 0,
        0,
        len(bad_cols),
        ", ".join(bad_cols[:20]),
    )

    # ------------------------------------------------------------
    # 6. Corpus summaries
    # ------------------------------------------------------------
    corpus_summary = (
        macro.groupby("corpus")
        .agg(
            n_texts=("text_id", "count"),
            total_raw=("intra_total_raw", "sum"),
            supported_total_raw=("supported_intra_total_raw", "sum"),
            mean_total_per_1000=("intra_total_per_1000", "mean"),
            median_total_per_1000=("intra_total_per_1000", "median"),
            mean_supported_per_1000=("supported_intra_total_per_1000", "mean"),
            median_supported_per_1000=("supported_intra_total_per_1000", "median"),
        )
        .reset_index()
    )

    mismatch_rows = merged[
        (~merged["broad_total_match"]) | (~merged["supported_total_match"])
    ].copy()

    checks_df = pd.DataFrame(checks)

    with pd.ExcelWriter(REPORT_FILE, engine="openpyxl") as writer:
        checks_df.to_excel(writer, sheet_name="Validation checks", index=False)
        corpus_summary.to_excel(writer, sheet_name="Corpus summary", index=False)
        formula_df.to_excel(writer, sheet_name="Formula checks", index=False)
        mismatch_rows.head(1000).to_excel(writer, sheet_name="Mismatches sample", index=False)

    print("\nVALIDATION CHECKS")
    print(checks_df.to_string(index=False))

    print("\nCORPUS SUMMARY")
    print(corpus_summary.to_string(index=False))

    print("\nWrote:", REPORT_FILE)


if __name__ == "__main__":
    main()