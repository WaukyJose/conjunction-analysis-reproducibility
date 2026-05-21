from pathlib import Path
import re
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
from resources.halliday_paragraph_dict import HALLIDAY_CONJUNCTIONS

OUT_DIR = BASE_DIR / "outputs" / "index_descriptions"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "interparagraph_index_description_ENHANCEMENT.xlsx"
PRIMARY_DENOMINATOR = "Total words in the text; reported per 1,000 words."
SECONDARY_DENOMINATOR = (
    "Eligible paragraph starts, calculated as paragraph_count_text - 1; "
    "reported as a rate/proportion of possible paragraph-initial positions."
)
DEFAULT_OUTPUT_FILE = "03_interparagraph_subcategory_indices.xlsx"
RECOMMENDED_OUTPUT_FILE = "advanced_connector_indices/connector_indices_enhancement.xlsx"
ADVANCED_OUTPUT_FILE = "advanced_connector_indices/connector_indices_ENHANCEMENT.xlsx"


def slugify(text):
    text = str(text).lower().strip()
    text = text.replace("causal-conditional", "causal_conditional")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def clean_sheet_name(name):
    name = re.sub(r"[\[\]\:\*\?\/\\]", "_", name)
    return name[:31]


def output_columns(index_name):
    return {
        "Output raw column": f"{index_name}_raw",
        "Output per 1,000 column": f"{index_name}_per_1000",
        "Output per eligible paragraph start column": (
            f"{index_name}_per_eligible_paragraph_start"
        ),
        "Recommended output file": RECOMMENDED_OUTPUT_FILE,
    }


def readable_in_text_name(path_parts, connector):

    lower_parts = [p.lower().replace("_", " ").replace("-", " ") for p in path_parts[1:]]

    return "paragraph-initial " + " ".join(lower_parts) + f" “{connector}”"


def flatten_enhancement():

    rows_by_tab = {}

    enhancement = HALLIDAY_CONJUNCTIONS["Enhancement"]

    def recurse(node, path):

        if isinstance(node, list):

            # One Excel tab per final dictionary path.

            # Example:

            # Enhancement > Spatio-temporal > Simple > Following

            tab = "_".join(path)

            rows_by_tab.setdefault(tab, [])

            for connector in node:

                index_name = (

                    "interparagraph_"

                    + "_".join(slugify(p) for p in path)

                    + "_"

                    + slugify(connector)

                )

                rows_by_tab[tab].append({

                    "Index name": index_name,

                    "In-text name": readable_in_text_name(path, connector),

                    "Connector": connector,

                    "Index description": (

                        f"Number of paragraph-initial occurrences of “{connector}” "

                        f"functioning as {' > '.join(path)}."

                    ),

                    "Primary denominator": PRIMARY_DENOMINATOR,

                    "Secondary denominator": SECONDARY_DENOMINATOR,

                    "Support status": "Supported",

                    "Dictionary path": " > ".join(path),

                    **output_columns(index_name),

                })

        elif isinstance(node, dict):

            for key, value in node.items():

                recurse(value, path + [key])

    recurse(enhancement, ["Enhancement"])

    return rows_by_tab


def main():

    rows_by_tab = flatten_enhancement()

    overview_rows = []
    overview_note = (
        "This workbook documents the full inter-paragraph Enhancement dictionary inventory. "
        "Some items may be excluded from the supported parser output through operational "
        "filtering or marker-confidence rules."
    )

    def make_unique_sheet_names(tab_names):
        """
        Excel sheet names are limited to 31 characters.
        This function creates unique shortened names and preserves the mapping.
        """
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

    sheet_name_map = make_unique_sheet_names(rows_by_tab.keys())

    for tab, rows in rows_by_tab.items():

        overview_rows.append({

            "Logical tab name": tab,

            "Excel sheet name": sheet_name_map[tab],

            "Number of connector-level indices": len(rows),

            "Macro category": "Enhancement",

            "Description": "Inter-paragraph Enhancement markers from halliday_paragraph_dict.py",
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

        for tab, rows in rows_by_tab.items():

            df = pd.DataFrame(rows)

            df.to_excel(

                writer,

                sheet_name=sheet_name_map[tab],

                index=False,

            )

    print("Wrote:", OUT_FILE)

    print("\nTabs:")

    for tab, rows in rows_by_tab.items():

        print(f"- {tab}: {len(rows)} rows")


if __name__ == "__main__":

    main()
