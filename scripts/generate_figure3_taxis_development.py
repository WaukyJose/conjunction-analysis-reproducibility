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
import pandas as pd


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

FIGURE_BASENAME = "figure3_taxis_development_supported_intrasentential"
DOCX_IMAGE_PATH = "word/media/image3.png"

CORPUS_ORDER = ["COREFL", "EFCAMDAT", "GiG"]
GROUP_ORDER = {
    "COREFL": ["A1", "A2", "B1", "B2", "C1", "C2"],
    "EFCAMDAT": ["A1", "A2", "B1", "B2", "C1"],
    "GiG": ["2", "4", "6", "9", "11"],
}
X_LABELS = {
    "COREFL": "CEFR level",
    "EFCAMDAT": "CEFR level",
    "GiG": "Year group",
}


def load_group_percentages() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    df["group"] = df["group"].astype(str)
    df["parataxis_raw"] = (
        df["supported_intra_paratactic_elaboration_raw"]
        + df["supported_intra_paratactic_extension_raw"]
        + df["supported_intra_paratactic_enhancement_raw"]
    )
    df["hypotaxis_raw"] = (
        df["supported_intra_hypotactic_elaboration_raw"]
        + df["supported_intra_hypotactic_extension_raw"]
        + df["supported_intra_hypotactic_enhancement_raw"]
    )

    grouped = (
        df.groupby(["corpus", "group"], as_index=False)[["parataxis_raw", "hypotaxis_raw"]]
        .sum()
    )
    grouped["total_raw"] = grouped["parataxis_raw"] + grouped["hypotaxis_raw"]
    grouped["parataxis_pct"] = grouped["parataxis_raw"] / grouped["total_raw"] * 100
    grouped["hypotaxis_pct"] = grouped["hypotaxis_raw"] / grouped["total_raw"] * 100

    for corpus in CORPUS_ORDER:
        missing = sorted(set(GROUP_ORDER[corpus]) - set(grouped.loc[grouped["corpus"] == corpus, "group"]))
        if missing:
            raise ValueError(f"Missing expected groups for {corpus}: {missing}")
    return grouped


def draw_figure(grouped: pd.DataFrame):
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(2969 / 300, 1304 / 300),
        dpi=300,
        sharey=True,
    )

    for ax, corpus in zip(axes, CORPUS_ORDER):
        order = GROUP_ORDER[corpus]
        sub = (
            grouped[grouped["corpus"] == corpus]
            .set_index("group")
            .loc[order]
            .reset_index()
        )
        x = range(len(sub))
        ax.plot(
            x,
            sub["parataxis_pct"],
            marker="o",
            linewidth=1.6,
            markersize=4.5,
            label="Parataxis",
            color="#1f77b4",
        )
        ax.plot(
            x,
            sub["hypotaxis_pct"],
            marker="o",
            linewidth=1.6,
            markersize=4.5,
            label="Hypotaxis",
            color="#ff7f0e",
        )
        ax.set_title(corpus, fontsize=11, pad=4)
        ax.set_xticks(list(x))
        ax.set_xticklabels(order, fontsize=8)
        ax.set_xlabel(X_LABELS[corpus], fontsize=8)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 20, 40, 60, 80, 100])
        ax.grid(axis="y", color="#e6e6e6", linewidth=0.7)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

    axes[0].set_ylabel("Detected intra-sentential conjunctions (%)", fontsize=8)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, 0.98),
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.91), w_pad=1.0)
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

    grouped = load_group_percentages()
    grouped.to_csv(OUT_DIR / f"{FIGURE_BASENAME}_percentages.csv", index=False)

    fig = draw_figure(grouped)
    png_file = OUT_DIR / f"{FIGURE_BASENAME}.png"
    svg_file = OUT_DIR / f"{FIGURE_BASENAME}.svg"
    pdf_file = OUT_DIR / f"{FIGURE_BASENAME}.pdf"
    manuscript_png = MANUSCRIPT_MEDIA_DIR / "image3.png"

    fig.savefig(png_file, dpi=300)
    fig.savefig(svg_file)
    fig.savefig(pdf_file)
    fig.savefig(manuscript_png, dpi=300)
    plt.close(fig)

    replace_docx_image(manuscript_png)

    print(f"Input: {INPUT_FILE}")
    print(grouped.to_string(index=False))
    print(f"PNG: {png_file}")
    print(f"SVG: {svg_file}")
    print(f"PDF: {pdf_file}")
    print(f"Manuscript PNG: {manuscript_png}")
    if MANUSCRIPT_DOCX.exists():
        print(f"Updated embedded DOCX image: {MANUSCRIPT_DOCX}:{DOCX_IMAGE_PATH}")


if __name__ == "__main__":
    main()
