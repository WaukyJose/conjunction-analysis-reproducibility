"""Create a limited precision-style manual audit sample.

This script samples detected conjunction cases from the finalized token-level
case outputs. It is designed for precision-style checking of detected cases
only; it does not estimate recall and does not rerun any parser pipeline.

By default, context is truncated so that exported validation files do not
redistribute full learner texts. Use --context-mode none to omit context
entirely, or --context-mode full only for local/private review.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = BASE_DIR / "validation"
DEFAULT_SAMPLE_SIZE = 100
DEFAULT_RANDOM_SEED = 42
DEFAULT_CONTEXT_CHARS = 220
DEFAULT_OUTPUT_NAME = "manual_precision_audit_sample_with_context.csv"


LEVEL_SOURCES = {
    "intra_sentential": {
        "candidates": [
            BASE_DIR
            / "outputs"
            / "v2_intrasentential_full"
            / "v2_intrasentential_full_cases.csv",
        ],
        "support_col": "is_priming_supported",
        "position_cols": ["sentence_index", "connector_start_char", "connector_end_char"],
        "context_cols": ["sentence"],
    },
    "inter_sentential": {
        "candidates": [
            BASE_DIR
            / "outputs"
            / "v2_intersentential_full"
            / "v2_intersentential_full_cases.csv",
        ],
        "support_col": "is_intersentential_supported",
        "position_cols": ["sentence_index", "sentence_start_cleaned"],
        "context_cols": ["previous_sentence", "current_sentence"],
    },
    "inter_paragraph": {
        "candidates": [
            BASE_DIR
            / "outputs"
            / "v2_interparagraph_full"
            / "v2_interparagraph_full_cases.csv",
        ],
        "support_col": "is_interparagraph_supported",
        "position_cols": ["paragraph_index", "paragraph_start_cleaned"],
        "context_cols": ["previous_paragraph", "current_paragraph"],
    },
}


MANUAL_COLUMNS = [
    "is_conjunction_use",
    "position_correct",
    "function_acceptable",
    "main_error_type",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sample detected conjunction cases for manual precision-style audit."
    )
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    parser.add_argument(
        "--context-mode",
        choices=["truncated", "none", "full"],
        default="truncated",
        help="How much learner-text context to export. Default: truncated.",
    )
    parser.add_argument(
        "--context-chars",
        type=int,
        default=DEFAULT_CONTEXT_CHARS,
        help="Maximum characters per context field when --context-mode=truncated.",
    )
    parser.add_argument(
        "--include-unsupported",
        action="store_true",
        help="Sample all candidate detections instead of final supported detections only.",
    )
    parser.add_argument(
        "--no-intra-precedence-alignment",
        action="store_true",
        help=(
            "Do not align intra-sentential and/but/or display labels with the "
            "final Extension-preference precedence refinement."
        ),
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--output-name", default=DEFAULT_OUTPUT_NAME)
    return parser.parse_args()


def first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    formatted = "\n".join(str(path) for path in paths)
    raise FileNotFoundError(f"No candidate source file found:\n{formatted}")


def as_supported_mask(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0).astype(int).eq(1)
    return series.astype(str).str.strip().str.lower().isin({"1", "true", "yes", "y"})


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).split())


def split_sentences(text: object) -> list[str]:
    """Mirror the lightweight sentence splitter used by the V2 runners."""
    if not isinstance(text, str):
        return []

    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []

    parts = re.split(r"(?<=[.!?])\s+(?=[\"'“”‘’A-Z0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def split_paragraphs(text: object) -> list[str]:
    """Mirror the newline paragraph splitter used by the inter-paragraph runner."""
    if not isinstance(text, str):
        return []

    text = text.strip()
    if not text:
        return []

    parts = re.split(r"\n+", text)
    parts = [re.sub(r"\s+", " ", p.strip()) for p in parts]
    return [p for p in parts if p]


def bracket_first_connector(text: object, connector: object) -> str:
    text_clean = clean_text(text)
    connector_clean = clean_text(connector)
    if not text_clean or not connector_clean:
        return text_clean

    pattern = re.compile(rf"(?<!\w)({re.escape(connector_clean)})(?!\w)", re.IGNORECASE)
    match = pattern.search(text_clean)
    if not match:
        pattern = re.compile(re.escape(connector_clean), re.IGNORECASE)
        match = pattern.search(text_clean)
    if not match:
        return text_clean
    return f"{text_clean[:match.start()]}[{match.group(1)}]{text_clean[match.end():]}"


def truncate_text(value: object, max_chars: int, from_end: bool = False) -> str:
    text = clean_text(value)
    if len(text) <= max_chars:
        return text
    if from_end:
        return "..." + text[-max_chars:]
    return text[:max_chars] + "..."


def format_context_value(
    value: object, mode: str, max_chars: int, from_end: bool = False
) -> str:
    if mode == "none":
        return ""
    if mode == "full":
        return clean_text(value)
    return truncate_text(value, max_chars, from_end=from_end)


def make_intra_context(row: pd.Series, mode: str, max_chars: int) -> str:
    if mode == "none":
        return ""

    sentence = clean_text(row.get("sentence", ""))
    if not sentence:
        return ""

    if mode == "full":
        return sentence

    start = row.get("connector_start_char")
    end = row.get("connector_end_char")
    try:
        start_i = int(start)
        end_i = int(end)
    except (TypeError, ValueError):
        return truncate_text(sentence, max_chars)

    left = sentence[max(0, start_i - max_chars // 2) : start_i]
    hit = sentence[start_i:end_i]
    right = sentence[end_i : end_i + max_chars // 2]
    prefix = "..." if start_i > max_chars // 2 else ""
    suffix = "..." if end_i + max_chars // 2 < len(sentence) else ""
    return f"{prefix}{left}[{hit}]{right}{suffix}"


def join_nonempty(parts: list[str], sep: str = " / ") -> str:
    return sep.join(part for part in parts if part)


def bracket_initial_connector(text: object, connector: object) -> str:
    text_clean = clean_text(text)
    connector_clean = clean_text(connector)
    if not text_clean or not connector_clean:
        return text_clean

    leading_label = (
        r"(?:[-•\*\s\"'“”‘’\(\[\{]+|\(?[0-9]+[\).\:\-]?\s*|"
        r"[A-Za-z][\).\:\-]\s*)*"
    )
    match = re.match(
        rf"^({leading_label})({re.escape(connector_clean)})(\b|[,\.;:\?!])?",
        text_clean,
        flags=re.IGNORECASE,
    )
    if not match:
        return text_clean

    suffix = match.group(3) or ""
    return (
        f"{match.group(1)}[{match.group(2)}]{suffix}"
        f"{text_clean[match.end():]}"
    )


def has_bracketed_connector(value: object) -> bool:
    return bool(re.search(r"\[[^\]]+\]", clean_text(value)))


def add_context_columns(
    df: pd.DataFrame, discourse_level: str, mode: str, max_chars: int
) -> pd.DataFrame:
    out = df.copy()
    if mode == "none":
        out["context"] = ""
        return out

    if discourse_level == "intra_sentential":
        out["context"] = out.apply(make_intra_context, axis=1, args=(mode, max_chars))
        out["context_snippet"] = out["context"]
        return out

    if discourse_level == "inter_sentential":
        out["previous_sentence"] = out.get("previous_sentence", "").map(
            lambda x: "" if mode == "none" else clean_text(x)
        )
        out["current_sentence"] = out.get("current_sentence", "").map(
            lambda x: "" if mode == "none" else clean_text(x)
        )
        out["previous_context"] = out["previous_sentence"]
        out["current_context"] = out["current_sentence"]
        out["context_snippet"] = out.apply(
            lambda row: join_nonempty(
                [
                    row.get("previous_sentence", ""),
                    bracket_initial_connector(
                        row.get("current_sentence", ""),
                        row.get("detected_item", ""),
                    ),
                ],
                sep=" || ",
            ),
            axis=1,
        )
        return out

    if discourse_level == "inter_paragraph":
        out["previous_paragraph"] = out.get("previous_paragraph", "").map(
            lambda x: "" if mode == "none" else clean_text(x)
        )
        out["current_paragraph"] = out.get("current_paragraph", "").map(
            lambda x: "" if mode == "none" else clean_text(x)
        )
        out["previous_context"] = out["previous_paragraph"]
        out["current_context"] = out["current_paragraph"]
        out["previous_paragraph_snippet"] = out["previous_paragraph"].map(
            lambda x: format_context_value(x, mode, max_chars, from_end=True)
        )
        out["current_paragraph_snippet"] = out["current_paragraph"].map(
            lambda x: format_context_value(x, mode, max_chars)
        )
        out["previous_paragraph_start"] = out["previous_paragraph_snippet"]
        out["current_paragraph_start"] = out["current_paragraph_snippet"]
        out["paragraph_context"] = out.apply(
            lambda row: join_nonempty(
                [
                    row.get("previous_paragraph_snippet", ""),
                    bracket_initial_connector(
                        row.get("current_paragraph", ""),
                        row.get("detected_item", ""),
                    ),
                ],
                sep=" || ",
            ),
            axis=1,
        )
        out["context_snippet"] = out["paragraph_context"]
        return out

    raise ValueError(f"Unknown discourse level: {discourse_level}")


def align_intra_precedence_display_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Align manual-audit labels with the final intra-sentential precedence rule.

    The token-level cases file is the only source with sentence context, but some
    high-frequency coordination forms may retain their original first-match
    Enhancement labels there. For manual auditing of the finalized analysis, the
    exported sample should show the corrected Extension-preference labels while
    preserving the original labels in separate columns.
    """

    out = df.copy()
    for col in ["macro_category", "path_2", "path_3", "path_4", "path_5"]:
        if col in out.columns:
            out[f"original_{col}"] = out[col]

    if "detected_item" not in out.columns or "macro_category" not in out.columns:
        return out

    item = out["detected_item"].astype(str).str.lower().str.strip()
    taxis = (
        out["taxis"].astype(str).str.lower().str.strip()
        if "taxis" in out.columns
        else pd.Series("", index=out.index)
    )
    mask = item.isin({"and", "but", "or"}) & taxis.eq("paratactic")

    out.loc[mask, "macro_category"] = "Extension"
    if "path_2" in out.columns:
        out.loc[mask & item.eq("and"), "path_2"] = "Addition"
        out.loc[mask & item.eq("but"), "path_2"] = "Adversative"
        out.loc[mask & item.eq("or"), "path_2"] = "Variation"
    if "path_3" in out.columns:
        out.loc[mask & item.eq("or"), "path_3"] = "Alternative"
        out.loc[mask & item.isin({"and", "but"}), "path_3"] = pd.NA
    if "path_4" in out.columns:
        out.loc[mask, "path_4"] = "paratactic"

    out["precedence_alignment_applied"] = mask.astype(int)
    return out


def choose_columns(df: pd.DataFrame, source_cfg: dict) -> list[str]:
    preferred = [
        "audit_id",
        "discourse_level",
        "corpus",
        "text_id",
        "group",
        "detected_item",
        "macro_category",
        "path_2",
        "path_3",
        "path_4",
        "path_5",
        "original_macro_category",
        "original_path_2",
        "original_path_3",
        "original_path_4",
        "original_path_5",
        "precedence_alignment_applied",
        "taxis",
        "context",
        "context_snippet",
        "previous_sentence",
        "current_sentence",
        "paragraph_context",
        "previous_paragraph_start",
        "current_paragraph_start",
        "previous_paragraph_snippet",
        "current_paragraph_snippet",
        "previous_paragraph",
        "current_paragraph",
        "previous_context",
        "current_context",
        "sentence_index",
        "paragraph_index",
        "connector_start_char",
        "connector_end_char",
        "sentence_start_cleaned",
        "paragraph_start_cleaned",
        "intersentential_marker_type",
        "interparagraph_marker_type",
        "priming_decision",
        "priming_confidence",
        "intersentential_confidence",
        "interparagraph_confidence",
        "word_count_text",
        "sentence_count_text",
        "paragraph_count_text",
        "source_output_file",
        "source_file",
        source_cfg["support_col"],
        "algorithm_notes",
    ]
    return [col for col in preferred if col in df.columns]


def load_and_sample(
    discourse_level: str,
    source_cfg: dict,
    sample_size: int,
    random_seed: int,
    include_unsupported: bool,
    context_mode: str,
    context_chars: int,
    align_intra_precedence: bool,
) -> tuple[pd.DataFrame, dict]:
    source_path = first_existing(source_cfg["candidates"])
    df = pd.read_csv(source_path, low_memory=False)
    original_rows = len(df)

    support_col = source_cfg["support_col"]
    if not include_unsupported and support_col in df.columns:
        df = df[as_supported_mask(df[support_col])].copy()

    sampled_rows = min(sample_size, len(df))
    sample = df.sample(n=sampled_rows, random_state=random_seed).copy()
    sample.insert(0, "discourse_level", discourse_level)
    sample["source_output_file"] = str(source_path.relative_to(BASE_DIR))
    sample = add_context_columns(sample, discourse_level, context_mode, context_chars)
    if discourse_level == "intra_sentential" and align_intra_precedence:
        sample = align_intra_precedence_display_labels(sample)

    info = {
        "discourse_level": discourse_level,
        "source_file": str(source_path.relative_to(BASE_DIR)),
        "rows_in_source": original_rows,
        "rows_after_supported_filter": len(df),
        "sampled_rows": sampled_rows,
        "support_column": support_col if support_col in sample.columns else "",
        "precedence_alignment_applied": (
            int(sample.get("precedence_alignment_applied", pd.Series(dtype=int)).sum())
            if discourse_level == "intra_sentential"
            else 0
        ),
    }
    sample = sample[choose_columns(sample, source_cfg)]
    return sample, info


def build_coverage_report(out: pd.DataFrame) -> dict[str, object]:
    context = out.get("context_snippet", pd.Series("", index=out.index)).fillna("").astype(str)
    report: dict[str, object] = {}
    for level in ["intra_sentential", "inter_sentential", "inter_paragraph"]:
        mask = out["discourse_level"].eq(level)
        report[level] = int((mask & context.str.strip().ne("")).sum())
    return report


def print_coverage_report(report: dict[str, object]) -> None:
    print("Context snippet non-empty coverage by discourse_level:")
    print(f"intra_sentential     {report['intra_sentential']}")
    print(f"inter_sentential    {report['inter_sentential']}")
    print(f"inter_paragraph     {report['inter_paragraph']}")


def write_readme(
    path: Path,
    source_info: list[dict],
    sample_size: int,
    random_seed: int,
    context_mode: str,
    include_unsupported: bool,
) -> None:
    lines = [
        "# Manual precision-style conjunction audit sample",
        "",
        "This file supports a limited diagnostic audit of detected conjunction cases only.",
        "It estimates precision-style reliability for detections, position assignment,",
        "and functional classification. It does not estimate recall because non-detected",
        "conjunctions are not sampled.",
        "",
        "## Sampling design",
        "",
        f"- Target sample: up to {sample_size} detected cases per discourse level.",
        f"- Random seed: {random_seed}.",
        f"- Context export mode: `{context_mode}`.",
        f"- Supported-only detections: `{not include_unsupported}`.",
        "- Intra-sentential precedence alignment: corrected display labels are used for paratactic `and`, `but`, and `or` where applicable; original labels are retained in `original_*` columns.",
        "- Discourse levels: intra-sentential, inter-sentential, inter-paragraph.",
        "",
        "## Source files",
        "",
    ]
    for info in source_info:
        lines.extend(
            [
                f"### {info['discourse_level']}",
                f"- Source: `{info['source_file']}`",
                f"- Rows in source: {info['rows_in_source']}",
                f"- Rows after supported filter: {info['rows_after_supported_filter']}",
                f"- Sampled rows: {info['sampled_rows']}",
                f"- Support column: `{info['support_column']}`",
                f"- Rows with intra-sentential precedence display alignment: {info['precedence_alignment_applied']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Manual annotation columns",
            "",
            "- `is_conjunction_use`: code `1` if the detected item is a conjunction use in context, otherwise `0`.",
            "- `position_correct`: code `1` if the discourse-position assignment is acceptable, otherwise `0`.",
            "- `function_acceptable`: code `1` if the Hallidayan macro/subcategory assignment is acceptable, otherwise `0`.",
            "- `main_error_type`: use one of `false_positive`, `wrong_position`, `wrong_function`, `ambiguous`, or `other`.",
            "- `notes`: optional short comment.",
            "",
            "For strict functional precision, the summary script counts a case as correct only when",
            "`is_conjunction_use`, `position_correct`, and `function_acceptable` are all coded `1`.",
            "",
            "## Privacy note",
            "",
            "The default sample uses truncated context windows rather than full learner texts.",
            "For public redistribution, review the context fields and remove or further truncate",
            "them if required by corpus licensing or privacy rules.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    samples = []
    source_info = []
    for discourse_level, source_cfg in LEVEL_SOURCES.items():
        sample, info = load_and_sample(
            discourse_level=discourse_level,
            source_cfg=source_cfg,
            sample_size=args.sample_size,
            random_seed=args.random_seed,
            include_unsupported=args.include_unsupported,
            context_mode=args.context_mode,
            context_chars=args.context_chars,
            align_intra_precedence=not args.no_intra_precedence_alignment,
        )
        samples.append(sample)
        source_info.append(info)

    out = pd.concat(samples, ignore_index=True, sort=False)
    out.insert(0, "audit_id", [f"MPA_{i + 1:04d}" for i in range(len(out))])

    for col in MANUAL_COLUMNS:
        out[col] = ""

    coverage_report = build_coverage_report(out)

    output_csv = args.out_dir / args.output_name
    output_readme = args.out_dir / "manual_precision_audit_readme.md"
    out.to_csv(output_csv, index=False)
    write_readme(
        output_readme,
        source_info,
        sample_size=args.sample_size,
        random_seed=args.random_seed,
        context_mode=args.context_mode,
        include_unsupported=args.include_unsupported,
    )

    print(f"Wrote: {output_csv}")
    print(f"Wrote: {output_readme}")
    print("Sampled rows by discourse level:")
    print(out["discourse_level"].value_counts().sort_index().to_string())
    print_coverage_report(coverage_report)


if __name__ == "__main__":
    main()
