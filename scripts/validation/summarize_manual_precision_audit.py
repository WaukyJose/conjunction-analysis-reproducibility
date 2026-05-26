"""Summarize completed manual precision-style audit annotations.

Input is the CSV produced by create_manual_precision_audit_sample.py after the
manual annotation columns have been completed. The script computes detection,
position, and strict functional precision by discourse level, plus error-type
counts. It does not modify parser outputs or rerun any analysis pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_IN_FILE = BASE_DIR / "validation" / "manual_precision_audit_sample.csv"
DEFAULT_OUT_DIR = BASE_DIR / "validation"

ANNOTATION_COLUMNS = [
    "is_conjunction_use",
    "position_correct",
    "function_acceptable",
    "main_error_type",
]

VALID_ERROR_TYPES = {
    "false_positive",
    "wrong_position",
    "wrong_function",
    "ambiguous",
    "other",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize completed manual precision-style audit annotations."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_IN_FILE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def numeric_annotation(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.strip().str.lower()
    mapped = cleaned.map(
        {
            "1": 1.0,
            "1.0": 1.0,
            "true": 1.0,
            "yes": 1.0,
            "y": 1.0,
            "0": 0.0,
            "0.0": 0.0,
            "false": 0.0,
            "no": 0.0,
            "n": 0.0,
            "": pd.NA,
            "nan": pd.NA,
            "none": pd.NA,
        }
    )
    return pd.to_numeric(mapped, errors="coerce")


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in ["discourse_level", *ANNOTATION_COLUMNS] if col not in df]
    if missing:
        raise ValueError(f"Input file is missing required columns: {missing}")


def summarize_group(group: pd.DataFrame) -> pd.Series:
    is_conj = numeric_annotation(group["is_conjunction_use"])
    position = numeric_annotation(group["position_correct"])
    function = numeric_annotation(group["function_acceptable"])
    strict = ((is_conj == 1) & (position == 1) & (function == 1)).astype(float)
    strict[(is_conj.isna()) | (position.isna()) | (function.isna())] = pd.NA

    return pd.Series(
        {
            "sampled_rows": len(group),
            "annotated_is_conjunction_use_n": int(is_conj.notna().sum()),
            "annotated_position_correct_n": int(position.notna().sum()),
            "annotated_function_acceptable_n": int(function.notna().sum()),
            "fully_annotated_n": int(
                (is_conj.notna() & position.notna() & function.notna()).sum()
            ),
            "detection_precision": is_conj.mean(skipna=True),
            "position_precision": position.mean(skipna=True),
            "strict_functional_precision": strict.mean(skipna=True),
        }
    )


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    by_level = (
        df.groupby("discourse_level", dropna=False)
        .apply(summarize_group, include_groups=False)
        .reset_index()
    )
    overall = summarize_group(df).to_frame().T
    overall.insert(0, "discourse_level", "overall")
    summary = pd.concat([by_level, overall], ignore_index=True)
    count_cols = [
        "sampled_rows",
        "annotated_is_conjunction_use_n",
        "annotated_position_correct_n",
        "annotated_function_acceptable_n",
        "fully_annotated_n",
    ]
    for col in count_cols:
        summary[col] = summary[col].astype("Int64")
    return summary


def build_error_counts(df: pd.DataFrame) -> pd.DataFrame:
    error = df[["discourse_level", "main_error_type"]].copy()
    error["main_error_type"] = error["main_error_type"].astype(str).str.strip().str.lower()
    error = error[error["main_error_type"].ne("") & error["main_error_type"].ne("nan")]
    if error.empty:
        return pd.DataFrame(columns=["discourse_level", "main_error_type", "count"])

    counts = (
        error.groupby(["discourse_level", "main_error_type"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["discourse_level", "count", "main_error_type"], ascending=[True, False, True])
    )
    return counts


def write_markdown(
    path: Path, input_file: Path, summary: pd.DataFrame, error_counts: pd.DataFrame, df: pd.DataFrame
) -> None:
    invalid_error_types = sorted(
        {
            str(value).strip().lower()
            for value in df["main_error_type"].dropna()
            if str(value).strip()
            and str(value).strip().lower() not in VALID_ERROR_TYPES
        }
    )

    lines = [
        "# Manual precision-style audit summary",
        "",
        f"- Input file: `{input_file}`",
        "- Scope: detected conjunction cases only.",
        "- Recall is not estimated.",
        "",
        "## Precision summaries",
        "",
        summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Error-type counts",
        "",
    ]
    if error_counts.empty:
        lines.append("No error types were coded.")
    else:
        lines.append(error_counts.to_markdown(index=False))

    lines.extend(
        [
            "",
            "## Metric definitions",
            "",
            "- `detection_precision`: mean of `is_conjunction_use`.",
            "- `position_precision`: mean of `position_correct`.",
            "- `strict_functional_precision`: mean of cases where `is_conjunction_use`, `position_correct`, and `function_acceptable` are all `1`.",
            "",
            "## Annotation completeness",
            "",
            "Rows with blank annotation cells are excluded from the relevant mean.",
        ]
    )

    if invalid_error_types:
        lines.extend(
            [
                "",
                "## Warning",
                "",
                "The following `main_error_type` values are outside the recommended set",
                f"{sorted(VALID_ERROR_TYPES)}:",
                "",
                ", ".join(invalid_error_types),
            ]
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input, low_memory=False)
    validate_columns(df)

    summary = build_summary(df)
    error_counts = build_error_counts(df)

    summary_csv = args.out_dir / "manual_precision_audit_summary.csv"
    error_csv = args.out_dir / "manual_precision_audit_error_types.csv"
    summary_md = args.out_dir / "manual_precision_audit_summary.md"

    summary.to_csv(summary_csv, index=False)
    error_counts.to_csv(error_csv, index=False)
    write_markdown(summary_md, args.input, summary, error_counts, df)

    print(f"Wrote: {summary_csv}")
    print(f"Wrote: {error_csv}")
    print(f"Wrote: {summary_md}")


if __name__ == "__main__":
    main()
