from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

os.environ.setdefault(
    "MPLCONFIGDIR",
    "/private/tmp/conjunction_research_matplotlib_config",
)
os.environ.setdefault(
    "XDG_CACHE_HOME",
    "/private/tmp/conjunction_research_cache",
)

import matplotlib.pyplot as plt
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "v2_intrasentential_full"
    / "v2_intrasentential_full_supported_text_indices.csv"
)
OUT_DIR = BASE_DIR / "outputs" / "figures"
MANUSCRIPT_MEDIA_DIR = BASE_DIR / "manuscript_review" / "wordcut" / "media"
MANUSCRIPT_DOCX = BASE_DIR / "manuscript_review" / "wordcut" / "current.docx"

FIGURE_BASENAME = "figure2_macro_categories_within_taxis_supported_intrasentential"
DOCX_IMAGE_PATH = "word/media/image2.png"

CORPORA = ["COREFL", "EFCAMDAT", "GiG"]
TAXES = ["paratactic", "hypotactic"]
TAXIS_TITLES = {"paratactic": "Parataxis", "hypotactic": "Hypotaxis"}
MACROS = ["extension", "enhancement", "elaboration"]
MACRO_LABELS = {
    "extension": "Extension",
    "enhancement": "Enhancement",
    "elaboration": "Elaboration",
}
COLORS = {
    "extension": "#1f77b4",
    "enhancement": "#ff7f0e",
    "elaboration": "#2ca02c",
}


def supported_raw_column(taxis: str, macro: str) -> str:
    return f"supported_intra_{taxis}_{macro}_raw"


def load_supported_counts() -> pd.DataFrame:
    required = ["corpus"] + [
        supported_raw_column(taxis, macro) for taxis in TAXES for macro in MACROS
    ]
    df = pd.read_csv(INPUT_FILE, usecols=required, low_memory=False)
    missing_corpora = sorted(set(CORPORA) - set(df["corpus"].dropna()))
    if missing_corpora:
        raise ValueError(f"Missing expected corpora in supported input: {missing_corpora}")
    return df


def compute_percentages(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for taxis in TAXES:
        for corpus in CORPORA:
            corpus_df = df[df["corpus"] == corpus]
            counts = {
                macro: int(corpus_df[supported_raw_column(taxis, macro)].sum())
                for macro in MACROS
            }
            total = sum(counts.values())
            if total == 0:
                raise ValueError(f"No supported {taxis} cases found for {corpus}")
            pct_sum = 0.0
            for macro in MACROS:
                pct = counts[macro] / total * 100
                pct_sum += pct
                rows.append(
                    {
                        "corpus": corpus,
                        "taxis": taxis,
                        "macro_category": MACRO_LABELS[macro],
                        "raw_count": counts[macro],
                        "taxis_total_raw": total,
                        "percentage_within_taxis": pct,
                    }
                )
            if not np.isclose(pct_sum, 100.0, atol=1e-9):
                raise ValueError(
                    f"Percentages for {corpus} {taxis} sum to {pct_sum:.12f}"
                )
    return pd.DataFrame(rows)


def draw_figure(percentages: pd.DataFrame):
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(1901 / 300, 1324 / 300),
        dpi=300,
        sharey=True,
    )
    x = np.arange(len(CORPORA))
    width = 0.24
    offsets = [-width, 0, width]

    for ax, taxis in zip(axes, TAXES):
        taxis_df = percentages[percentages["taxis"] == taxis]
        for macro, offset in zip(MACROS, offsets):
            values = [
                taxis_df[
                    (taxis_df["corpus"] == corpus)
                    & (taxis_df["macro_category"] == MACRO_LABELS[macro])
                ]["percentage_within_taxis"].iloc[0]
                for corpus in CORPORA
            ]
            ax.bar(
                x + offset,
                values,
                width,
                label=MACRO_LABELS[macro],
                color=COLORS[macro],
            )

        ax.set_title(TAXIS_TITLES[taxis], fontsize=15, pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(CORPORA, fontsize=10)
        ax.set_ylim(0, 100)
        ax.set_yticks(np.arange(0, 101, 20))
        ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

    axes[0].set_ylabel("Percentage within taxis (%)", fontsize=12)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 1.0),
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return fig


def replace_docx_image(image_file: Path) -> None:
    if not MANUSCRIPT_DOCX.exists():
        return

    with tempfile.NamedTemporaryFile(
        suffix=".docx", delete=False, dir=MANUSCRIPT_DOCX.parent
    ) as tmp:
        tmp_path = Path(tmp.name)

    with ZipFile(MANUSCRIPT_DOCX, "r") as zin, ZipFile(
        tmp_path, "w", ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            if item.filename == DOCX_IMAGE_PATH:
                data = image_file.read_bytes()
            else:
                data = zin.read(item.filename)
            zout.writestr(item, data)

    shutil.move(tmp_path, MANUSCRIPT_DOCX)


def main() -> None:
    df = load_supported_counts()
    percentages = compute_percentages(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANUSCRIPT_MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    csv_file = OUT_DIR / f"{FIGURE_BASENAME}_percentages.csv"
    percentages.to_csv(csv_file, index=False)

    fig = draw_figure(percentages)
    png_file = OUT_DIR / f"{FIGURE_BASENAME}.png"
    svg_file = OUT_DIR / f"{FIGURE_BASENAME}.svg"
    pdf_file = OUT_DIR / f"{FIGURE_BASENAME}.pdf"
    manuscript_png = MANUSCRIPT_MEDIA_DIR / "image2.png"

    fig.savefig(png_file, dpi=300)
    fig.savefig(svg_file)
    fig.savefig(pdf_file)
    fig.savefig(manuscript_png, dpi=300)
    plt.close(fig)

    replace_docx_image(manuscript_png)

    print(f"Input: {INPUT_FILE}")
    for taxis in TAXES:
        print(TAXIS_TITLES[taxis])
        for corpus in CORPORA:
            subset = percentages[
                (percentages["taxis"] == taxis)
                & (percentages["corpus"] == corpus)
            ]
            parts = [
                f"{row.macro_category}={row.percentage_within_taxis:.2f}%"
                for row in subset.itertuples()
            ]
            print(f"  {corpus}: {', '.join(parts)}, sum={subset['percentage_within_taxis'].sum():.6f}%")
    print(f"Percentages CSV: {csv_file}")
    print(f"PNG: {png_file}")
    print(f"SVG: {svg_file}")
    print(f"PDF: {pdf_file}")
    print(f"Manuscript PNG: {manuscript_png}")
    if MANUSCRIPT_DOCX.exists():
        print(f"Updated embedded DOCX image: {MANUSCRIPT_DOCX}:{DOCX_IMAGE_PATH}")


if __name__ == "__main__":
    main()
