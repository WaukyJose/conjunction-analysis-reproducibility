from pathlib import Path
import re
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
from resources.halliday_paragraph_dict import HALLIDAY_CONJUNCTIONS

OUT_DIR = BASE_DIR / "outputs" / "index_descriptions"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "interparagraph_index_description_EXTENSION.xlsx"
PRIMARY_DENOMINATOR = "Total words in the text; reported per 1,000 words."
SECONDARY_DENOMINATOR = (
    "Eligible paragraph starts, calculated as paragraph_count_text - 1; "
    "reported as a rate/proportion of possible paragraph-initial positions."
)
DEFAULT_OUTPUT_FILE = "03_interparagraph_subcategory_indices.xlsx"
RECOMMENDED_OUTPUT_FILE = "advanced_connector_indices/connector_indices_extension.xlsx"
ADVANCED_OUTPUT_FILE = "advanced_connector_indices/connector_indices_EXTENSION.xlsx"


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


def output_columns(index_name):
    return {
        "Output raw column": f"{index_name}_raw",
        "Output per 1,000 column": f"{index_name}_per_1000",
        "Output per eligible paragraph start column": (
            f"{index_name}_per_eligible_paragraph_start"
        ),
        "Recommended output file": RECOMMENDED_OUTPUT_FILE,
    }


def flatten_extension():
    rows_by_tab = {}

    extension = HALLIDAY_CONJUNCTIONS["Extension"]

    for path_2, value_2 in extension.items():

        # Case 1: direct list, e.g. Adversative, Stance_Markers
        if isinstance(value_2, list):
            tab = f"Extension_{path_2}"
            rows_by_tab.setdefault(tab, [])

            for connector in value_2:
                index_name = (
                    "interparagraph_extension_"
                    f"{slugify(path_2)}_"
                    f"{slugify(connector)}"
                )

                in_text_name = f"paragraph-initial {path_2.lower()} {connector}"

                support_status = (
                    "Excluded from supported index; retained in broad output"
                    if path_2 == "Stance_Markers"
                    else "Supported"
                )

                rows_by_tab[tab].append({
                    "Index name": index_name,
                    "In-text name": in_text_name,
                    "Connector": connector,
                    "Index description": (
                        f"Number of paragraph-initial occurrences of “{connector}” "
                        f"functioning as Extension > {path_2}."
                    ),
                    "Primary denominator": PRIMARY_DENOMINATOR,
                    "Secondary denominator": SECONDARY_DENOMINATOR,
                    "Support status": support_status,
                    "Dictionary path": f"Extension > {path_2}",
                    **output_columns(index_name),
                })

        # Case 2: nested dict, e.g. Addition > Positive / Negative
        elif isinstance(value_2, dict):
            for path_3, connectors in value_2.items():
                tab = f"Extension_{path_2}_{path_3}"
                rows_by_tab.setdefault(tab, [])

                for connector in connectors:
                    index_name = (
                        "interparagraph_extension_"
                        f"{slugify(path_2)}_"
                        f"{slugify(path_3)}_"
                        f"{slugify(connector)}"
                    )

                    in_text_name = (
                        f"paragraph-initial {path_2.lower()} "
                        f"{path_3.lower()} {connector}"
                    )

                    rows_by_tab[tab].append({
                        "Index name": index_name,
                        "In-text name": in_text_name,
                        "Connector": connector,
                        "Index description": (
                            f"Number of paragraph-initial occurrences of “{connector}” "
                            f"functioning as Extension > {path_2} > {path_3}."
                        ),
                        "Primary denominator": PRIMARY_DENOMINATOR,
                        "Secondary denominator": SECONDARY_DENOMINATOR,
                        "Support status": "Supported",
                        "Dictionary path": f"Extension > {path_2} > {path_3}",
                        **output_columns(index_name),
                    })

    return rows_by_tab


def main():
    rows_by_tab = flatten_extension()

    overview_rows = []
    overview_note = (
        "This workbook documents the full inter-paragraph Extension dictionary inventory. "
        "Some items may be excluded from the supported parser output through operational "
        "filtering or marker-confidence rules."
    )
    sheet_name_map = make_unique_sheet_names(rows_by_tab.keys())

    for tab, rows in rows_by_tab.items():
        overview_rows.append({
            "Logical tab name": tab,
            "Excel sheet name": sheet_name_map[tab],
            "Number of connector-level indices": len(rows),
            "Macro category": "Extension",
            "Description": "Inter-paragraph Extension markers from halliday_paragraph_dict.py",
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
