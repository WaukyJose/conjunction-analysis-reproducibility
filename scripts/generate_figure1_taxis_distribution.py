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


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "outputs" / "figures"
MANUSCRIPT_MEDIA_DIR = BASE_DIR / "manuscript_review" / "wordcut" / "media"
MANUSCRIPT_DOCX = BASE_DIR / "manuscript_review" / "wordcut" / "current.docx"

FIGURE_BASENAME = "figure1_taxis_distribution_supported_intrasentential"
DOCX_IMAGE_PATH = "word/media/image1.png"

CORPORA = ["COREFL", "EFCAMDAT", "GiG"]
PARATAXIS = np.array([44.4, 53.6, 34.3])
HYPOTAXIS = np.array([55.6, 46.4, 65.7])


def verify_percentages() -> None:
    expected = np.full(len(CORPORA), 100.0)
    totals = PARATAXIS + HYPOTAXIS
    if not np.allclose(totals, expected, atol=1e-9):
        details = ", ".join(
            f"{corpus}: {total:.10g}" for corpus, total in zip(CORPORA, totals)
        )
        raise ValueError(f"Parataxis + hypotaxis percentages must equal 100: {details}")


def draw_figure():
    x = np.arange(len(CORPORA))
    width = 0.32

    fig, ax = plt.subplots(figsize=(1379 / 220, 881 / 220), dpi=220)
    ax.bar(x - width / 2, PARATAXIS, width, label="Parataxis", color="#1f77b4")
    ax.bar(x + width / 2, HYPOTAXIS, width, label="Hypotaxis", color="#ff7f0e")

    ax.set_ylabel("Detected intra-sentential conjunctions (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(CORPORA)
    ax.set_ylim(0, 100)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.10),
        ncol=2,
        frameon=False,
    )

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
    verify_percentages()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANUSCRIPT_MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    fig = draw_figure()

    png_file = OUT_DIR / f"{FIGURE_BASENAME}.png"
    svg_file = OUT_DIR / f"{FIGURE_BASENAME}.svg"
    pdf_file = OUT_DIR / f"{FIGURE_BASENAME}.pdf"
    manuscript_png = MANUSCRIPT_MEDIA_DIR / "image1.png"

    fig.savefig(png_file, dpi=220)
    fig.savefig(svg_file)
    fig.savefig(pdf_file)
    fig.savefig(manuscript_png, dpi=220)
    plt.close(fig)

    replace_docx_image(manuscript_png)

    for corpus, parataxis, hypotaxis in zip(CORPORA, PARATAXIS, HYPOTAXIS):
        print(
            f"{corpus}: parataxis={parataxis:.1f}, "
            f"hypotaxis={hypotaxis:.1f}, sum={parataxis + hypotaxis:.1f}"
        )
    print(f"PNG: {png_file}")
    print(f"SVG: {svg_file}")
    print(f"PDF: {pdf_file}")
    print(f"Manuscript PNG: {manuscript_png}")
    if MANUSCRIPT_DOCX.exists():
        print(f"Updated embedded DOCX image: {MANUSCRIPT_DOCX}:{DOCX_IMAGE_PATH}")


if __name__ == "__main__":
    main()
