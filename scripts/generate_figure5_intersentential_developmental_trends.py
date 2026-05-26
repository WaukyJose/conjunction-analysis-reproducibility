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
    / "v2_intersentential_full"
    / "v2_intersentential_full_supported_text_indices.csv"
)
OUT_DIR = BASE_DIR / "outputs" / "figures"
MANUSCRIPT_MEDIA_DIR = BASE_DIR / "manuscript_review" / "wordcut" / "media"
MANUSCRIPT_DOCX = BASE_DIR / "manuscript_review" / "wordcut" / "current.docx"

FIGURE_BASENAME = "figure5_intersentential_developmental_trends"
DOCX_IMAGE_PATH = "word/media/image5.png"

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


def load_group_medians() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    df["group"] = df["group"].astype(str)

    rows = []
    for corpus in CORPUS_ORDER:
        corpus_df = df[df["corpus"] == corpus]
        for group in GROUP_ORDER[corpus]:
            group_df = corpus_df[corpus_df["group"] == group]
            if group_df.empty:
                raise ValueError(f"Missing group {group} for {corpus}")
            rows.append(
                {
                    "corpus": corpus,
                    "group": group,
                    "n": int(len(group_df)),
                    "zero_density_rows": int(
                        group_df["supported_inter_sentential_total_raw"].eq(0).sum()
                    ),
                    "median_density_per_1000": float(
                        group_df["supported_inter_sentential_total_per_1000"].median()
                    ),
                    "mean_density_per_1000": float(
                        group_df["supported_inter_sentential_total_per_1000"].mean()
                    ),
                }
            )
    return pd.DataFrame(rows)


def draw_figure(summary: pd.DataFrame):
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(1380 / 300, 460 / 300),
        dpi=300,
        sharey=True,
    )

    for ax, corpus in zip(axes, CORPUS_ORDER):
        sub = summary[summary["corpus"] == corpus].set_index("group").loc[
            GROUP_ORDER[corpus]
        ].reset_index()
        x = range(len(sub))
        ax.plot(
            x,
            sub["median_density_per_1000"],
            marker="o",
            linewidth=1.2,
            markersize=3,
            color="#1f77b4",
        )
        ax.set_title(corpus, fontsize=8, pad=4)
        ax.set_xticks(list(x))
        ax.set_xticklabels(GROUP_ORDER[corpus], fontsize=7)
        ax.set_xlabel(X_LABELS[corpus], fontsize=7)
        ax.grid(True, linestyle="--", color="#d9d9d9", linewidth=0.6)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_linewidth(0.7)

    axes[0].set_ylabel(
        "Inter-sentential conjunctions\nper 1,000 words (median)",
        fontsize=6,
        labelpad=8,
    )
    axes[0].set_ylim(0, 17.5)
    fig.subplots_adjust(left=0.15, right=0.985, bottom=0.28, top=0.82, wspace=0.18)
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

    summary = load_group_medians()
    csv_file = OUT_DIR / f"{FIGURE_BASENAME}_medians.csv"
    summary.to_csv(csv_file, index=False)

    fig = draw_figure(summary)
    png_file = OUT_DIR / f"{FIGURE_BASENAME}.png"
    svg_file = OUT_DIR / f"{FIGURE_BASENAME}.svg"
    pdf_file = OUT_DIR / f"{FIGURE_BASENAME}.pdf"
    manuscript_png = MANUSCRIPT_MEDIA_DIR / "image5.png"

    fig.savefig(png_file, dpi=300)
    fig.savefig(svg_file)
    fig.savefig(pdf_file)
    fig.savefig(manuscript_png, dpi=300)
    plt.close(fig)

    replace_docx_image(manuscript_png)

    print(f"Input: {INPUT_FILE}")
    print(summary.to_string(index=False))
    print(f"Medians CSV: {csv_file}")
    print(f"PNG: {png_file}")
    print(f"SVG: {svg_file}")
    print(f"PDF: {pdf_file}")
    print(f"Manuscript PNG: {manuscript_png}")
    if MANUSCRIPT_DOCX.exists():
        print(f"Updated embedded DOCX image: {MANUSCRIPT_DOCX}:{DOCX_IMAGE_PATH}")


if __name__ == "__main__":
    main()
