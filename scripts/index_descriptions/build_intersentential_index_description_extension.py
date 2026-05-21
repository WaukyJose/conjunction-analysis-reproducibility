from pathlib import Path
import re
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from resources.halliday_intersent_dic import HALLIDAY_CONJUNCTIONS


MACRO = "Extension"
MACRO_LOWER = "extension"
OUT_DIR = BASE_DIR / "outputs" / "index_descriptions"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "intersentential_index_description_EXTENSION.xlsx"

PRIMARY_DENOMINATOR = "Total words in the text; reported per 1,000 words."
SECONDARY_DENOMINATOR = (
    "Eligible sentence starts, calculated as sentence_count_text - 1; "
    "reported as a rate/proportion of possible sentence-initial positions."
)
DEFAULT_OUTPUT_FILE = "03_intersentential_subcategory_indices.xlsx"
RECOMMENDED_OUTPUT_FILE = "advanced_connector_indices/connector_indices_extension.xlsx"
ADVANCED_OUTPUT_FILE = "advanced_connector_indices/connector_indices_extension.xlsx"
LOW_CONFIDENCE_CONNECTORS = {
    "maybe",
    "perhaps",
    "really",
    "never",
    "fortunately",
    "unfortunately",
}


def slugify(text):
    text = str(text).lower().strip()
    text = text.replace("causal-conditional", "causal_conditional")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def clean_sheet_name(name):
    name = re.sub(r"[\[\]\:\*\?\/\\]", "_", name)
    return name[:31]


def make_unique_sheet_names(tab_names):
    used = {}
    used_names = set()
    mapping = {}
    for tab in tab_names:
        base = clean_sheet_name(tab)
        if base not in used and base not in used_names:
            used[base] = 1
            mapping[tab] = base
            used_names.add(base)
        else:
            used[base] = used.get(base, 1)
            while True:
                used[base] += 1
                suffix = f"_{used[base]:02d}"
                sheet_name = base[:31 - len(suffix)] + suffix
                if sheet_name not in used_names:
                    mapping[tab] = sheet_name
                    used_names.add(sheet_name)
                    break
    return mapping


def readable_in_text_name(path_parts, connector):
    lower_parts = [
        p.lower().replace("_", " ").replace("-", " ")
        for p in path_parts[1:]
    ]
    return "sentence-initial " + " ".join(lower_parts) + f" “{connector}”"


def support_status(connector):
    if connector.lower().strip() in LOW_CONFIDENCE_CONNECTORS:
        return "Excluded from supported index; retained in broad output"
    return "Supported"


def output_columns(index_name):
    return {
        "Output raw column": f"{index_name}_raw",
        "Output per 1,000 column": f"{index_name}_per_1000",
        "Output per eligible sentence start column": (
            f"{index_name}_per_eligible_sentence_start"
        ),
        "Recommended output file": RECOMMENDED_OUTPUT_FILE,
    }


def flatten_macro():
    rows_by_tab = {}

    def recurse(node, path):
        if isinstance(node, list):
            tab = "_".join(path)
            rows_by_tab.setdefault(tab, [])
            for connector in node:
                index_name = (
                    "intersentential_"
                    + "_".join(slugify(part) for part in path)
                    + "_"
                    + slugify(connector)
                )
                rows_by_tab[tab].append({
                    "Index name": index_name,
                    "In-text name": readable_in_text_name(path, connector),
                    "Connector": connector,
                    "Index description": (
                        f"Number of sentence-initial occurrences of “{connector}” "
                        f"functioning as {' > '.join(path)}."
                    ),
                    "Primary denominator": PRIMARY_DENOMINATOR,
                    "Secondary denominator": SECONDARY_DENOMINATOR,
                    "Support status": support_status(connector),
                    "Dictionary path": " > ".join(path),
                    **output_columns(index_name),
                })
        elif isinstance(node, dict):
            for key, value in node.items():
                recurse(value, path + [key])

    recurse(HALLIDAY_CONJUNCTIONS[MACRO], [MACRO])
    return rows_by_tab


def main():
    rows_by_tab = flatten_macro()
    sheet_name_map = make_unique_sheet_names(rows_by_tab.keys())
    overview_note = (
        f"This workbook documents the full inter-sentential {MACRO} dictionary inventory. "
        "Some items may be excluded from the supported parser output through operational "
        "filtering or marker-confidence rules."
    )
    overview_rows = []
    for tab, rows in rows_by_tab.items():
        overview_rows.append({
            "Logical tab name": tab,
            "Excel sheet name": sheet_name_map[tab],
            "Number of connector-level indices": len(rows),
            "Macro category": MACRO,
            "Description": f"Inter-sentential {MACRO} markers from the Halliday dictionary.",
            "Operational note": overview_note,
            "Default output file": DEFAULT_OUTPUT_FILE,
            "Advanced connector-level output file": ADVANCED_OUTPUT_FILE,
        })

    with pd.ExcelWriter(OUT_FILE, engine="openpyxl") as writer:
        pd.DataFrame(overview_rows).to_excel(
            writer,
            sheet_name="Overview",
            index=False,
        )
        writer.sheets["Overview"].freeze_panes = "A2"
        for tab, rows in rows_by_tab.items():
            sheet_name = sheet_name_map[tab]
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)
            writer.sheets[sheet_name].freeze_panes = "A2"

    print("Wrote:", OUT_FILE)
    print("Sheets:", len(rows_by_tab) + 1)
    print("Connector-level rows:", sum(len(rows) for rows in rows_by_tab.values()))


if __name__ == "__main__":
    main()
