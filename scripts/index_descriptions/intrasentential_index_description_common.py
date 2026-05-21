from pathlib import Path
import re
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from resources.halliday_intrasent_dic import INTRA_CLAUSE_CONJUNCTIONS


OUT_DIR = BASE_DIR / "outputs" / "index_descriptions"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CASES_FILE = BASE_DIR / "outputs" / "v2_intrasentential_full" / "v2_intrasentential_full_cases.csv"

PRIMARY_DENOMINATOR = "Total words in the text; reported per 1,000 words."
DEFAULT_OUTPUT_FILE = "03_intrasentential_subcategory_indices.xlsx"
PROBLEMATIC_MULTIFUNCTIONAL_FORMS = {
    "and",
    "or",
    "as",
    "since",
    "while",
    "when",
    "then",
    "so",
    "but",
    "yet",
    "still",
    "however",
    "thus",
    "whereas",
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


def observed_context_sensitive_connectors():
    if not CASES_FILE.exists():
        return set()
    cases = pd.read_csv(
        CASES_FILE,
        usecols=lambda col: col in {"detected_item", "is_priming_supported"},
        low_memory=False,
    )
    if "detected_item" not in cases.columns or "is_priming_supported" not in cases.columns:
        return set()
    unsupported = cases[cases["is_priming_supported"] == 0]
    return set(unsupported["detected_item"].dropna().str.lower().str.strip())


def support_status(connector, context_sensitive_connectors):
    connector_lower = str(connector).lower().strip()
    if (
        connector_lower in PROBLEMATIC_MULTIFUNCTIONAL_FORMS
        or connector_lower in context_sensitive_connectors
    ):
        return "Broad output; support depends on priming/contextual decision"
    return "Supported by default"


def split_taxis(path_parts):
    taxis = "unspecified"
    labels = []
    for part in path_parts:
        if part in {"paratactic", "hypotactic"}:
            taxis = part
        else:
            labels.append(part)
    return taxis, labels


def readable_in_text_name(taxis, path_labels, connector):
    lower_parts = [
        part.lower().replace("_", " ").replace("-", " ")
        for part in path_labels[1:]
    ]
    return "intra-sentential " + taxis + " " + " ".join(lower_parts) + f" “{connector}”"


def output_columns(index_name, recommended_output_file):
    return {
        "Output raw column": f"{index_name}_raw",
        "Output per 1,000 column": f"{index_name}_per_1000",
        "Recommended output file": recommended_output_file,
    }


def iter_connector_rows(macro):
    def recurse(node, path):
        if isinstance(node, list):
            taxis, path_labels = split_taxis(path)
            tab = "_".join(path_labels)
            for connector in node:
                yield tab, taxis, path_labels, connector
        elif isinstance(node, dict):
            for key, value in node.items():
                yield from recurse(value, path + [key])

    yield from recurse(INTRA_CLAUSE_CONJUNCTIONS[macro], [macro])


def build_rows_by_tab(macro):
    context_sensitive_connectors = observed_context_sensitive_connectors()
    macro_lower = slugify(macro)
    recommended_output_file = (
        f"advanced_connector_indices/connector_indices_{macro_lower}.xlsx"
    )
    rows_by_tab = {}

    for tab, taxis, path_labels, connector in iter_connector_rows(macro):
        rows_by_tab.setdefault(tab, [])
        index_parts = [taxis] + path_labels + [connector]
        index_name = "intrasentential_" + "_".join(slugify(part) for part in index_parts)
        dictionary_path = " > ".join(path_labels)
        rows_by_tab[tab].append({
            "Index name": index_name,
            "In-text name": readable_in_text_name(taxis, path_labels, connector),
            "Connector": connector,
            "Taxis": taxis,
            "Index description": (
                f"Number of intra-sentential occurrences of “{connector}” "
                f"functioning as {dictionary_path} with {taxis} taxis."
            ),
            "Primary denominator": PRIMARY_DENOMINATOR,
            "Support status": support_status(connector, context_sensitive_connectors),
            "Dictionary path": dictionary_path,
            **output_columns(index_name, recommended_output_file),
        })

    return rows_by_tab


def write_workbook(macro):
    macro_upper = macro.upper()
    macro_lower = slugify(macro)
    out_file = OUT_DIR / f"intrasentential_index_description_{macro_upper}.xlsx"
    rows_by_tab = build_rows_by_tab(macro)
    sheet_name_map = make_unique_sheet_names(rows_by_tab.keys())
    overview_note = (
        f"This workbook documents the full intra-sentential {macro} dictionary inventory. "
        "Some items may be excluded from the supported parser output through "
        "lexical-priming/contextual filtering."
    )
    overview_rows = []
    for tab, rows in rows_by_tab.items():
        overview_rows.append({
            "Logical tab name": tab,
            "Excel sheet name": sheet_name_map[tab],
            "Number of connector-level indices": len(rows),
            "Macro category": macro,
            "Description": (
                f"Intra-sentential {macro} markers from the intra-sentential "
                "Halliday dictionary."
            ),
            "Operational note": overview_note,
            "Default output file": DEFAULT_OUTPUT_FILE,
            "Advanced connector-level output file": (
                f"advanced_connector_indices/connector_indices_{macro_lower}.xlsx"
            ),
        })

    with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
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

    n_rows = sum(len(rows) for rows in rows_by_tab.values())
    print("Wrote:", out_file)
    print("Sheets:", len(rows_by_tab) + 1)
    print("Connector-level rows:", n_rows)
    return out_file, len(rows_by_tab) + 1, n_rows
