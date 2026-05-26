#!/usr/bin/env python3
"""Regenerate Figure 7 from corrected supported inter-paragraph text indices."""

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
BACKUP_DIR = ROOT / "outputs/backups/figure7_update_20260522"

PNG = FIG_DIR / "figure7_interparagraph_developmental_trends.png"
SVG = FIG_DIR / "figure7_interparagraph_developmental_trends.svg"
PDF = FIG_DIR / "figure7_interparagraph_developmental_trends.pdf"
VALUES = FIG_DIR / "figure7_interparagraph_developmental_trends_means.csv"
AUDIT = FIG_DIR / "figure7_interparagraph_developmental_trends_audit.csv"
AUDIT_MD = FIG_DIR / "figure7_interparagraph_developmental_trends_audit.md"

MANUSCRIPT_IMAGE = ROOT / "manuscript_review/wordcut/media/image7.png"
MANUSCRIPT_DOCX = ROOT / "manuscript_review/wordcut/current.docx"

DENSITY = "supported_interparagraph_total_per_1000"
TOTAL = "supported_interparagraph_total_raw"
ORDERS = {
    "COREFL": ["A1", "A2", "B1", "B2", "C1", "C2"],
    "GiG": ["2", "4", "6", "9", "11"],
}


def validate_and_prepare() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    required = {"corpus", "text_id", "group", DENSITY, TOTAL}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    unexpected = sorted(set(df["corpus"].dropna()) - set(ORDERS))
    if unexpected:
        raise ValueError(f"Unexpected corpora in source: {unexpected}")

    df = df[df["corpus"].isin(ORDERS)].copy()
    df["group_plot"] = df["group"].astype(str)

    for corpus, order in ORDERS.items():
        sub = df[df["corpus"].eq(corpus)]
        missing_groups = sorted(set(order) - set(sub["group_plot"].dropna()))
        unexpected_groups = sorted(set(sub["group_plot"].dropna()) - set(order))
        if missing_groups or unexpected_groups:
            raise ValueError(
                f"{corpus} group mismatch; missing={missing_groups}, unexpected={unexpected_groups}"
            )

    if df["group_plot"].isna().any():
        raise ValueError("Missing developmental metadata after group conversion")

    return df


def compute_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    audit_rows = []
    for corpus, order in ORDERS.items():
        sub = df[df["corpus"].eq(corpus)]
        audit_rows.append(
            {
                "corpus": corpus,
                "eligible_rows": int(len(sub)),
                "zero_density_rows": int(sub[TOTAL].eq(0).sum()),
                "missing_developmental_metadata": int(sub["group_plot"].isna().sum()),
                "supported_interparagraph_tokens": int(sub[TOTAL].sum()),
            }
        )

        for group in order:
            g = sub[sub["group_plot"].eq(group)]
            if g.empty:
                raise ValueError(f"No rows for {corpus} {group}")
            rows.append(
                {
                    "corpus": corpus,
                    "developmental_group": group,
                    "n": int(len(g)),
                    "zero_density_rows": int(g[TOTAL].eq(0).sum()),
                    "median_density_per_1000": float(g[DENSITY].median()),
                    "mean_density_per_1000": float(g[DENSITY].mean()),
                    "supported_interparagraph_tokens": int(g[TOTAL].sum()),
                }
            )

    audit = pd.DataFrame(audit_rows)
    audit.loc[len(audit)] = {
        "corpus": "TOTAL",
        "eligible_rows": int(audit["eligible_rows"].sum()),
        "zero_density_rows": int(audit["zero_density_rows"].sum()),
        "missing_developmental_metadata": int(audit["missing_developmental_metadata"].sum()),
        "supported_interparagraph_tokens": int(audit["supported_interparagraph_tokens"].sum()),
    }
    return pd.DataFrame(rows), audit


def plot(values_table: pd.DataFrame, output_paths: list[Path]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.19, 4.08), dpi=150, sharey=True)

    for ax, corpus in zip(axes, ["COREFL", "GiG"]):
        sub = values_table[values_table["corpus"].eq(corpus)]
        order = ORDERS[corpus]
        values = [
            sub[sub["developmental_group"].eq(group)]["mean_density_per_1000"].iloc[0]
            for group in order
        ]
        x = np.arange(len(order))
        ax.plot(x, values, marker="o", linewidth=1.6)
        ax.set_title(corpus)
        ax.set_xticks(x)
        ax.set_xticklabels(order)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_ylim(0, 20)
        if corpus == "COREFL":
            ax.set_xlabel("CEFR level")
            ax.set_ylabel("Inter-paragraph conjunctions\nper 1,000 words (mean)")
        else:
            ax.set_xlabel("Year group")

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
            if item.filename == "word/media/image7.png":
                zout.writestr(item, image_path.read_bytes())
                replaced = True
            else:
                zout.writestr(item, zin.read(item.filename))
        if not replaced:
            zout.write(image_path, "word/media/image7.png")

    shutil.move(tmp_path, docx_path)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    for path in [PNG, SVG, PDF, VALUES, AUDIT, AUDIT_MD, MANUSCRIPT_IMAGE, MANUSCRIPT_DOCX]:
        if path.exists():
            shutil.copy2(path, BACKUP_DIR / path.name)

    df = validate_and_prepare()
    values_table, audit = compute_tables(df)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        tmp_png = tmp_dir / PNG.name
        tmp_svg = tmp_dir / SVG.name
        tmp_pdf = tmp_dir / PDF.name
        plot(values_table, [tmp_png, tmp_svg, tmp_pdf])

        tmp_values = tmp_dir / VALUES.name
        tmp_audit = tmp_dir / AUDIT.name
        tmp_audit_md = tmp_dir / AUDIT_MD.name
        values_table.to_csv(tmp_values, index=False)
        audit.to_csv(tmp_audit, index=False)
        total = audit[audit["corpus"].eq("TOTAL")].iloc[0]
        tmp_audit_md.write_text(
            "\n".join(
                [
                    "# Figure 7 Inter-Paragraph Developmental Trend Audit",
                    "",
                    f"Source: `{SOURCE.relative_to(ROOT)}`",
                    "",
                    f"Total eligible rows: {int(total['eligible_rows'])}",
                    f"Zero-density rows preserved: {int(total['zero_density_rows'])}",
                    "EFCAMDAT excluded: yes",
                    "Parser rerun: no",
                    "Inferential statistics rerun: no",
                    "Means computed from zero-inclusive distributions: yes",
                    "Medians also exported in the means table for audit context: yes",
                    "",
                    audit.to_markdown(index=False),
                    "",
                    values_table.to_markdown(index=False, floatfmt=".6f"),
                    "",
                ]
            ),
            encoding="utf-8",
        )

        for src, dst in [
            (tmp_png, PNG),
            (tmp_svg, SVG),
            (tmp_pdf, PDF),
            (tmp_values, VALUES),
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
    print(f"Wrote {VALUES.relative_to(ROOT)}")
    print(f"Wrote {AUDIT.relative_to(ROOT)}")
    print(f"Wrote {AUDIT_MD.relative_to(ROOT)}")
    print(f"Wrote {MANUSCRIPT_IMAGE.relative_to(ROOT)}")
    if MANUSCRIPT_DOCX.exists():
        print(f"Updated {MANUSCRIPT_DOCX.relative_to(ROOT)}")
    print()
    print(values_table.to_string(index=False))
    print()
    print(audit.to_string(index=False))


if __name__ == "__main__":
    main()
