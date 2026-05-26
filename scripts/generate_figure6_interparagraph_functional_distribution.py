#!/usr/bin/env python3
"""Regenerate Figure 6 from corrected supported inter-paragraph outputs only."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/v2_interparagraph_full/v2_interparagraph_full_supported_text_indices.csv"
FIG_DIR = ROOT / "outputs/figures"
BACKUP_DIR = ROOT / "outputs/backups/figure6_update_20260522"

PNG = FIG_DIR / "figure6_interparagraph_functional_distribution.png"
SVG = FIG_DIR / "figure6_interparagraph_functional_distribution.svg"
PDF = FIG_DIR / "figure6_interparagraph_functional_distribution.pdf"
PERCENTAGES = FIG_DIR / "figure6_interparagraph_functional_distribution_percentages.csv"
AUDIT = FIG_DIR / "figure6_interparagraph_functional_distribution_audit.csv"
AUDIT_MD = FIG_DIR / "figure6_interparagraph_functional_distribution_audit.md"

MANUSCRIPT_IMAGE = ROOT / "manuscript_review/wordcut/media/image6.png"
MANUSCRIPT_DOCX = ROOT / "manuscript_review/wordcut/current.docx"

CATEGORY_COLUMNS = {
    "Extension": "supported_interparagraph_extension_raw",
    "Enhancement": "supported_interparagraph_enhancement_raw",
    "Elaboration": "supported_interparagraph_elaboration_raw",
}
TOTAL_COLUMN = "supported_interparagraph_total_raw"
CORPUS_ORDER = ["COREFL", "GiG"]


def validate_input(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "corpus",
        "text_id",
        "word_count_text",
        TOTAL_COLUMN,
        *CATEGORY_COLUMNS.values(),
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if "EFCAMDAT" in set(df["corpus"].dropna()):
        df = df[df["corpus"] != "EFCAMDAT"].copy()

    unexpected = sorted(set(df["corpus"].dropna()) - set(CORPUS_ORDER))
    if unexpected:
        raise ValueError(f"Unexpected corpora in inter-paragraph source: {unexpected}")

    category_sum = df[list(CATEGORY_COLUMNS.values())].sum(axis=1)
    if not category_sum.equals(df[TOTAL_COLUMN]):
        mismatch = int((category_sum != df[TOTAL_COLUMN]).sum())
        raise ValueError(f"Category totals do not equal {TOTAL_COLUMN} for {mismatch} rows")

    return df


def compute_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    audit_rows = []
    for corpus in CORPUS_ORDER:
        corpus_df = df[df["corpus"] == corpus]
        if corpus_df.empty:
            raise ValueError(f"No eligible rows found for {corpus}")

        counts = {category: int(corpus_df[column].sum()) for category, column in CATEGORY_COLUMNS.items()}
        total = int(corpus_df[TOTAL_COLUMN].sum())
        if total <= 0:
            raise ValueError(f"No inter-paragraph conjunction tokens for {corpus}")

        for category in CATEGORY_COLUMNS:
            rows.append(
                {
                    "corpus": corpus,
                    "halliday_expansion_category": category,
                    "tokens": counts[category],
                    "percentage": counts[category] / total * 100,
                }
            )

        audit_rows.append(
            {
                "corpus": corpus,
                "eligible_text_rows": int(len(corpus_df)),
                "zero_density_rows": int((corpus_df[TOTAL_COLUMN] == 0).sum()),
                "total_interparagraph_tokens": total,
                "extension_tokens": counts["Extension"],
                "enhancement_tokens": counts["Enhancement"],
                "elaboration_tokens": counts["Elaboration"],
                "percentage_sum": sum(counts.values()) / total * 100,
            }
        )

    percentages = pd.DataFrame(rows)
    audit = pd.DataFrame(audit_rows)

    pct_sums = percentages.groupby("corpus")["percentage"].sum()
    if not np.allclose(pct_sums.to_numpy(), 100.0, atol=1e-10):
        raise ValueError(f"Percentages do not sum to 100: {pct_sums.to_dict()}")

    return percentages, audit


def plot(percentages: pd.DataFrame, output_paths: list[Path]) -> None:
    categories = list(CATEGORY_COLUMNS)
    x = np.arange(len(CORPUS_ORDER))
    width = 0.235
    offsets = np.array([-width, 0, width])

    fig, ax = plt.subplots(figsize=(9.19, 5.75), dpi=150)
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    for i, category in enumerate(categories):
        values = [
            percentages[
                (percentages["corpus"] == corpus)
                & (percentages["halliday_expansion_category"] == category)
            ]["percentage"].iloc[0]
            for corpus in CORPUS_ORDER
        ]
        ax.bar(x + offsets[i], values, width, label=category, color=colors[i])

    ax.set_ylabel("Inter-paragraph conjunctions (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(CORPUS_ORDER)
    ax.set_ylim(0, 80)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(False)

    fig.tight_layout()
    for path in output_paths:
        fig.savefig(path)
    plt.close(fig)


def replace_docx_image(docx_path: Path, image_path: Path) -> None:
    if not docx_path.exists():
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp_path = Path(tmp.name)

    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp_path, "w") as zout:
        replaced = False
        for item in zin.infolist():
            if item.filename == "word/media/image6.png":
                zout.writestr(item, image_path.read_bytes())
                replaced = True
            else:
                zout.writestr(item, zin.read(item.filename))
        if not replaced:
            zout.write(image_path, "word/media/image6.png")

    shutil.move(tmp_path, docx_path)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    for path in [PNG, SVG, PDF, PERCENTAGES, AUDIT, AUDIT_MD, MANUSCRIPT_IMAGE, MANUSCRIPT_DOCX]:
        if path.exists():
            shutil.copy2(path, BACKUP_DIR / path.name)

    df = validate_input(pd.read_csv(SOURCE))
    percentages, audit = compute_tables(df)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        tmp_png = tmp_dir / PNG.name
        tmp_svg = tmp_dir / SVG.name
        tmp_pdf = tmp_dir / PDF.name
        plot(percentages, [tmp_png, tmp_svg, tmp_pdf])

        tmp_percentages = tmp_dir / PERCENTAGES.name
        tmp_audit = tmp_dir / AUDIT.name
        tmp_audit_md = tmp_dir / AUDIT_MD.name
        percentages.to_csv(tmp_percentages, index=False)
        audit.to_csv(tmp_audit, index=False)
        tmp_audit_md.write_text(
            "\n".join(
                [
                    "# Figure 6 Inter-Paragraph Functional Distribution Audit",
                    "",
                    f"Source: `{SOURCE.relative_to(ROOT)}`",
                    "",
                    "- Parser rerun: no",
                    "- Analysis regenerated: descriptive inter-paragraph functional distribution only",
                    "- EFCAMDAT excluded: yes",
                    f"- Total eligible rows: {int(audit['eligible_text_rows'].sum())}",
                    f"- Zero-density rows preserved: {int(audit['zero_density_rows'].sum())}",
                    "- Percentages sum to 100% within each corpus: yes",
                    "",
                    audit.to_markdown(index=False),
                    "",
                    percentages.to_markdown(index=False, floatfmt=".6f"),
                    "",
                ]
            ),
            encoding="utf-8",
        )

        for src, dst in [
            (tmp_png, PNG),
            (tmp_svg, SVG),
            (tmp_pdf, PDF),
            (tmp_percentages, PERCENTAGES),
            (tmp_audit, AUDIT),
            (tmp_audit_md, AUDIT_MD),
        ]:
            shutil.move(src, dst)

    MANUSCRIPT_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PNG, MANUSCRIPT_IMAGE)
    replace_docx_image(MANUSCRIPT_DOCX, PNG)

    print(f"Wrote {PNG.relative_to(ROOT)}")
    print(f"Wrote {SVG.relative_to(ROOT)}")
    print(f"Wrote {PDF.relative_to(ROOT)}")
    print(f"Wrote {PERCENTAGES.relative_to(ROOT)}")
    print(f"Wrote {AUDIT.relative_to(ROOT)}")
    print(f"Wrote {AUDIT_MD.relative_to(ROOT)}")
    print(f"Wrote {MANUSCRIPT_IMAGE.relative_to(ROOT)}")
    if MANUSCRIPT_DOCX.exists():
        print(f"Updated {MANUSCRIPT_DOCX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
