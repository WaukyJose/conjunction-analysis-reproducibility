from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_clean"
OUT_DIR = BASE_DIR / "outputs" / "data_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "EFCAMDAT": {
        "file": DATA_DIR / "efcamdat_clean.csv",
        "id_col": "writing_id",
        "text_col": "text_clean_preserveCase",
        "group_cols": ["cefr", "cefr_numeric", "level", "grade"],
    },
    "GiG": {
        "file": DATA_DIR / "gig_clean.csv",
        "id_col": "text_id",
        "text_col": "text_clean_preserveCase",
        "group_cols": ["year_group", "attainment_level", "genre", "discipline"],
    },
    "IELTS": {
        "file": DATA_DIR / "ielts_clean.csv",
        "id_col": "essay_id",
        "text_col": "text_clean_preserveCase",
        "group_cols": ["band", "cefr"],
    },
}


def audit_dataset(name, spec):
    path = spec["file"]
    id_col = spec["id_col"]
    text_col = spec["text_col"]
    group_cols = spec["group_cols"]

    print(f"\n{'=' * 80}")
    print(name)
    print(path)

    df = pd.read_csv(path, low_memory=False)

    report = {
        "corpus": name,
        "file": str(path),
        "n_rows": len(df),
        "n_columns": df.shape[1],
        "id_col": id_col,
        "text_col": text_col,
        "id_missing": df[id_col].isna().sum() if id_col in df.columns else "MISSING_COL",
        "id_unique": df[id_col].nunique() if id_col in df.columns else "MISSING_COL",
        "id_duplicates": len(df) - df[id_col].nunique() if id_col in df.columns else "MISSING_COL",
        "text_missing": df[text_col].isna().sum() if text_col in df.columns else "MISSING_COL",
    }

    if text_col in df.columns:
        text = df[text_col].fillna("").astype(str)
        wc = text.str.split().str.len()
        report.update({
            "wc_min": wc.min(),
            "wc_q1": wc.quantile(0.25),
            "wc_median": wc.median(),
            "wc_mean": wc.mean(),
            "wc_q3": wc.quantile(0.75),
            "wc_max": wc.max(),
            "n_under_20_words": int((wc < 20).sum()),
            "n_under_50_words": int((wc < 50).sum()),
            "n_with_newline": int(text.str.contains(r"\n", regex=True).sum()),
            "pct_with_newline": round(text.str.contains(r"\n", regex=True).mean() * 100, 2),
        })

    group_reports = []
    for col in group_cols:
        if col in df.columns:
            counts = df[col].value_counts(dropna=False).reset_index()
            counts.columns = [col, "n"]
            counts.insert(0, "corpus", name)
            counts.insert(1, "group_col", col)
            group_reports.append(counts)

    print("Rows:", report["n_rows"])
    print("Columns:", report["n_columns"])
    print("ID duplicates:", report["id_duplicates"])
    print("Text missing:", report["text_missing"])
    print("Word count median:", report.get("wc_median"))
    print("% texts with newline:", report.get("pct_with_newline"))

    sample = df[[c for c in [id_col, text_col] + group_cols if c in df.columns]].head(20)
    sample.to_csv(OUT_DIR / f"{name.lower()}_sample_20.csv", index=False)

    return report, group_reports


def main():
    reports = []
    all_group_reports = []

    for name, spec in DATASETS.items():
        report, group_reports = audit_dataset(name, spec)
        reports.append(report)
        all_group_reports.extend(group_reports)

    report_df = pd.DataFrame(reports)
    report_df.to_csv(OUT_DIR / "clean_dataset_audit_summary.csv", index=False)

    if all_group_reports:
        group_df = pd.concat(all_group_reports, ignore_index=True)
        group_df.to_csv(OUT_DIR / "clean_dataset_group_counts.csv", index=False)

    print(f"\nSaved audit outputs to: {OUT_DIR}")


if __name__ == "__main__":
    main()