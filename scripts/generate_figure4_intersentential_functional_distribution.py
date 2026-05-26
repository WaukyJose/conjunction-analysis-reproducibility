from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

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
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "v2_intersentential_full"
    / "v2_intersentential_full_supported_text_indices.csv"
)
OUT_DIR = BASE_DIR / "outputs" / "figures"
MANUSCRIPT_MEDIA_DIR = BASE_DIR / "manuscript_review" / "wordcut" / "media"
MANUSCRIPT_DOCX = BASE_DIR / "manuscript_review" / "wordcut" / "current.docx"

FIGURE_BASENAME = "figure4_intersentential_functional_distribution"
DOCX_IMAGE_PATH = "word/media/image4.png"

CORPORA = ["COREFL", "EFCAMDAT", "GiG"]
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


def load_percentages() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    rows = []
    for corpus in CORPORA:
        corpus_df = df[df["corpus"] == corpus]
        counts = {
            macro: int(corpus_df[f"supported_inter_sentential_{macro}_raw"].sum())
            for macro in MACROS
        }
        total = sum(counts.values())
        if total == 0:
            raise ValueError(f"No supported inter-sentential tokens found for {corpus}")
        for macro in MACROS:
            rows.append(
                {
                    "corpus": corpus,
                    "macro_category": MACRO_LABELS[macro],
                    "raw_count": counts[macro],
                    "total_raw": total,
                    "percentage": counts[macro] / total * 100,
                    "eligible_texts": int(len(corpus_df)),
                    "zero_density_rows": int(
                        corpus_df["supported_inter_sentential_total_raw"].eq(0).sum()
                    ),
                }
            )
    out = pd.DataFrame(rows)
    sums = out.groupby("corpus")["percentage"].sum()
    bad = sums[(sums - 100).abs() > 1e-9]
    if not bad.empty:
        raise ValueError(f"Percentages do not sum to 100: {bad.to_dict()}")
    return out


def draw_figure(percentages: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(1378 / 220, 766 / 220), dpi=220)
    x = np.arange(len(CORPORA))
    width = 0.25
    offsets = [-width, 0, width]

    for macro, offset in zip(MACROS, offsets):
        values = [
            percentages[
                (percentages["corpus"] == corpus)
                & (percentages["macro_category"] == MACRO_LABELS[macro])
            ]["percentage"].iloc[0]
            for corpus in CORPORA
        ]
        ax.bar(
            x + offset,
            values,
            width,
            label=MACRO_LABELS[macro],
            color=COLORS[macro],
        )

    ax.set_ylabel("Inter-sentential conjunctions (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(CORPORA)
    ax.set_ylim(0, 80)
    ax.set_yticks(np.arange(0, 81, 10))
    ax.legend(loc="upper right", frameon=True)

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    fig.tight_layout()
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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANUSCRIPT_MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    percentages = load_percentages()
    csv_file = OUT_DIR / f"{FIGURE_BASENAME}_percentages.csv"
    percentages.to_csv(csv_file, index=False)

    fig = draw_figure(percentages)
    png_file = OUT_DIR / f"{FIGURE_BASENAME}.png"
    svg_file = OUT_DIR / f"{FIGURE_BASENAME}.svg"
    pdf_file = OUT_DIR / f"{FIGURE_BASENAME}.pdf"
    manuscript_png = MANUSCRIPT_MEDIA_DIR / "image4.png"

    fig.savefig(png_file, dpi=220)
    fig.savefig(svg_file)
    fig.savefig(pdf_file)
    fig.savefig(manuscript_png, dpi=220)
    plt.close(fig)

    replace_docx_image(manuscript_png)

    print(f"Input: {INPUT_FILE}")
    print(percentages.to_string(index=False))
    print(f"Percentages CSV: {csv_file}")
    print(f"PNG: {png_file}")
    print(f"SVG: {svg_file}")
    print(f"PDF: {pdf_file}")
    print(f"Manuscript PNG: {manuscript_png}")
    if MANUSCRIPT_DOCX.exists():
        print(f"Updated embedded DOCX image: {MANUSCRIPT_DOCX}:{DOCX_IMAGE_PATH}")


if __name__ == "__main__":
    main()
