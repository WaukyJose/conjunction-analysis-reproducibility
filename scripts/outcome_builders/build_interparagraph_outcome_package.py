from pathlib import Path
import re
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from resources.halliday_paragraph_dict import HALLIDAY_CONJUNCTIONS


INPUT_DIR = BASE_DIR / "outputs" / "v2_interparagraph_full"
CASES_FILE = INPUT_DIR / "v2_interparagraph_full_cases.csv"
TEXT_COUNTS_FILE = INPUT_DIR / "v2_interparagraph_full_text_counts.csv"
DATASETS = {
    "COREFL": {
        "file": BASE_DIR / "data_filtered" / "corefl_v2_filtered.csv",
        "id_col": "text_id",
        "text_col": "text_clean_preserveCase",
        "group_col": "cefr",
    },
    "GiG": {
        "file": BASE_DIR / "data_filtered" / "gig_v2_filtered.csv",
        "id_col": "text_id",
        "text_col": "text_clean_preserveCase",
        "group_col": "year_group",
    },
}

OUT_DIR = BASE_DIR / "outputs" / "interparagraph_outputs"
ADVANCED_DIR = OUT_DIR / "advanced_connector_indices"

DIAGNOSTICS_FILE = OUT_DIR / "01_diagnostics.xlsx"
MACRO_FILE = OUT_DIR / "02_macro_indices.xlsx"
SUBCATEGORY_FILE = OUT_DIR / "03_subcategory_indices.xlsx"
CASES_EVIDENCE_FILE = OUT_DIR / "04_cases_evidence.xlsx"
CONNECTOR_FILES = {
    "Extension": ADVANCED_DIR / "connector_indices_extension.xlsx",
    "Elaboration": ADVANCED_DIR / "connector_indices_elaboration.xlsx",
    "Enhancement": ADVANCED_DIR / "connector_indices_enhancement.xlsx",
}

MACROS = ["Extension", "Elaboration", "Enhancement"]
KEY_COLUMNS = ["corpus", "text_id"]
BASE_TEXT_COLUMNS = [
    "corpus",
    "text_id",
    "filename",
    "group",
    "word_count_text",
    "paragraph_count_text",
    "eligible_paragraph_starts",
]
CASE_EVIDENCE_COLUMNS = [
    "corpus",
    "text_id",
    "group",
    "paragraph_index",
    "previous_paragraph",
    "current_paragraph",
    "detected_item",
    "macro_category",
    "path_2",
    "path_3",
    "path_4",
    "path_5",
    "paragraph_start_cleaned",
    "interparagraph_marker_type",
    "interparagraph_confidence",
    "is_interparagraph_supported",
    "interparagraph_notes",
    "word_count_text",
    "paragraph_count_text",
    "source_file",
    "algorithm_notes",
]


def slugify(text):
    text = str(text).lower().strip()
    text = text.replace("causal-conditional", "causal_conditional")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def is_blank(value):
    return pd.isna(value) or str(value).strip() == ""


def clean_path_part(value):
    if is_blank(value):
        return ""
    return str(value).strip()


def split_paragraphs(text):
    if not isinstance(text, str):
        return []
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"\n+", text)
    return [re.sub(r"\s+", " ", p.strip()) for p in parts if p.strip()]


def sentence_count_if_available(df):
    for col in ["sentence_count_text", "sentence_count", "n_sentences"]:
        if col in df.columns:
            return df[col]
    return pd.NA


def filename_or_text_id(df):
    filename = pd.Series(pd.NA, index=df.index, dtype="object")
    for col in ["filename", "file_name", "source_file", "file_id", "file_id_norm"]:
        if col in df.columns:
            filename = filename.fillna(df[col])
    return filename.fillna(df["text_id"])


def load_inputs():
    cases = pd.read_csv(CASES_FILE, low_memory=False)
    text_counts = pd.read_csv(TEXT_COUNTS_FILE, low_memory=False)

    cases["corpus"] = cases["corpus"].astype(str)
    cases["text_id"] = cases["text_id"].astype(str)
    text_counts["corpus"] = text_counts["corpus"].astype(str)
    text_counts["text_id"] = text_counts["text_id"].astype(str)
    return cases, text_counts


def build_text_metadata(corpus, spec):
    df = pd.read_csv(spec["file"], low_memory=False)
    df[spec["id_col"]] = df[spec["id_col"]].astype(str)
    paragraphs = df[spec["text_col"]].apply(split_paragraphs)
    texts = pd.DataFrame({
        "corpus": corpus,
        "text_id": df[spec["id_col"]],
        "filename": filename_or_text_id(df),
        "group": df[spec["group_col"]],
        "word_count_text": df["wc_preserve"],
        "sentence_count_text": sentence_count_if_available(df),
        "paragraph_count_text": paragraphs.apply(len),
    })
    texts["eligible_paragraph_starts"] = (
        texts["paragraph_count_text"].fillna(0).astype(int) - 1
    ).clip(lower=0)
    texts["eligible_for_interparagraph"] = texts["paragraph_count_text"] >= 2
    texts["diagnostic_note"] = texts["eligible_for_interparagraph"].map({
        True: "Eligible: paragraph breaks detected",
        False: "Not eligible: fewer than two paragraphs",
    })
    return texts


def build_all_text_metadata():
    return pd.concat(
        [
            build_text_metadata(corpus, spec)
            for corpus, spec in DATASETS.items()
        ],
        ignore_index=True,
    )


def add_rates(df, base_names):
    new_columns = {}
    for base in base_names:
        raw_col = f"{base}_raw"
        per_1000_col = f"{base}_per_1000"
        per_start_col = f"{base}_per_eligible_paragraph_start"
        if raw_col in df.columns:
            raw = df[raw_col].fillna(0).astype(int)
        else:
            raw = pd.Series(0, index=df.index, dtype="int64")
        new_columns[raw_col] = raw
        new_columns[per_1000_col] = (
            raw / df["word_count_text"] * 1000
        ).where(df["word_count_text"] > 0, 0)
        new_columns[per_start_col] = (
            raw / df["eligible_paragraph_starts"]
        ).where(df["eligible_paragraph_starts"] > 0, 0)

    replace_cols = [col for col in new_columns if col in df.columns]
    if replace_cols:
        df = df.drop(columns=replace_cols)
    return pd.concat([df, pd.DataFrame(new_columns, index=df.index)], axis=1)


def macro_base(macro, supported=False):
    prefix = "supported_" if supported else ""
    return f"{prefix}interparagraph_{slugify(macro)}"


def macro_total_base(supported=False):
    prefix = "supported_" if supported else ""
    return f"{prefix}interparagraph_total"


def path_base(macro, path_parts, connector=None, supported=False):
    prefix = "supported_" if supported else ""
    parts = [macro] + [part for part in path_parts if part]
    if connector is not None:
        parts.append(connector)
    return prefix + "interparagraph_" + "_".join(slugify(part) for part in parts)


def iter_dictionary_paths():
    def recurse(node, macro, path_parts):
        if isinstance(node, list):
            yield macro, path_parts, node
        elif isinstance(node, dict):
            for key, value in node.items():
                yield from recurse(value, macro, path_parts + [key])

    for macro in MACROS:
        yield from recurse(HALLIDAY_CONJUNCTIONS[macro], macro, [])


def dictionary_subcategory_bases():
    bases = []
    for macro, path_parts, _connectors in iter_dictionary_paths():
        bases.append(path_base(macro, path_parts))
    return list(dict.fromkeys(bases))


def dictionary_connector_bases_by_macro():
    bases_by_macro = {macro: [] for macro in MACROS}
    for macro, path_parts, connectors in iter_dictionary_paths():
        for connector in connectors:
            bases_by_macro[macro].append(path_base(macro, path_parts, connector))
    return {macro: list(dict.fromkeys(bases)) for macro, bases in bases_by_macro.items()}


def add_case_bases(cases):
    cases = cases.copy()
    path_cols = ["path_2", "path_3", "path_4", "path_5"]
    cases["macro_clean"] = cases["macro_category"].apply(clean_path_part)
    for col in path_cols:
        cases[f"{col}_clean"] = cases[col].apply(clean_path_part)
    cases["detected_item_clean"] = cases["detected_item"].apply(clean_path_part)

    cases["subcategory_base"] = cases.apply(
        lambda row: path_base(
            row["macro_clean"],
            [row[f"{col}_clean"] for col in path_cols],
        ),
        axis=1,
    )
    cases["connector_base"] = cases.apply(
        lambda row: path_base(
            row["macro_clean"],
            [row[f"{col}_clean"] for col in path_cols],
            row["detected_item_clean"],
        ),
        axis=1,
    )
    return cases


def wide_counts(cases, variable_col, expected_bases, supported=False):
    expected_cols = [f"{base}_raw" for base in expected_bases]
    if supported:
        cases = cases[cases["is_interparagraph_supported"] == 1].copy()
    if cases.empty:
        return pd.DataFrame(columns=KEY_COLUMNS + expected_cols)

    counts = (
        cases.groupby(KEY_COLUMNS + [variable_col])
        .size()
        .reset_index(name="raw_count")
    )
    counts["column"] = counts[variable_col] + "_raw"
    wide = (
        counts.pivot_table(
            index=KEY_COLUMNS,
            columns="column",
            values="raw_count",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )
    wide = (
        wide.set_index(KEY_COLUMNS)
        .reindex(columns=expected_cols, fill_value=0)
        .reset_index()
    )
    return wide


def merge_count_wide(base_df, wide):
    out = base_df.merge(wide, on=KEY_COLUMNS, how="left")
    raw_cols = [col for col in out.columns if col.endswith("_raw")]
    out[raw_cols] = out[raw_cols].fillna(0).astype(int)
    return out


def build_diagnostics(all_texts, cases, text_indices):
    counts = text_indices[[
        "corpus",
        "text_id",
        "interparagraph_total_raw",
        "supported_interparagraph_total_raw",
    ]].copy()
    diagnostics = all_texts.merge(counts, on=KEY_COLUMNS, how="left")
    for col in ["interparagraph_total_raw", "supported_interparagraph_total_raw"]:
        diagnostics[col] = diagnostics[col].fillna(0).astype(int)
    return diagnostics[[
        "corpus",
        "text_id",
        "filename",
        "group",
        "word_count_text",
        "sentence_count_text",
        "paragraph_count_text",
        "eligible_paragraph_starts",
        "eligible_for_interparagraph",
        "diagnostic_note",
        "interparagraph_total_raw",
        "supported_interparagraph_total_raw",
    ]]


def build_macro_indices(eligible_texts, cases):
    out = eligible_texts[BASE_TEXT_COLUMNS].copy()

    broad_counts = (
        cases.groupby(KEY_COLUMNS + ["macro_clean"])
        .size()
        .reset_index(name="raw_count")
    )
    supported_counts = (
        cases[cases["is_interparagraph_supported"] == 1]
        .groupby(KEY_COLUMNS + ["macro_clean"])
        .size()
        .reset_index(name="raw_count")
    )

    for macro in MACROS:
        base = macro_base(macro)
        values = broad_counts[broad_counts["macro_clean"] == macro][KEY_COLUMNS + ["raw_count"]]
        values = values.rename(columns={"raw_count": f"{base}_raw"})
        out = out.merge(values, on=KEY_COLUMNS, how="left")

        supported_base = macro_base(macro, supported=True)
        supported_values = supported_counts[
            supported_counts["macro_clean"] == macro
        ][KEY_COLUMNS + ["raw_count"]]
        supported_values = supported_values.rename(
            columns={"raw_count": f"{supported_base}_raw"}
        )
        out = out.merge(supported_values, on=KEY_COLUMNS, how="left")

    broad_bases = [macro_base(macro) for macro in MACROS]
    supported_bases = [macro_base(macro, supported=True) for macro in MACROS]
    raw_cols = [f"{base}_raw" for base in broad_bases + supported_bases]
    out[raw_cols] = out[raw_cols].fillna(0).astype(int)

    out[f"{macro_total_base()}_raw"] = out[[f"{base}_raw" for base in broad_bases]].sum(axis=1)
    out[f"{macro_total_base(True)}_raw"] = out[
        [f"{base}_raw" for base in supported_bases]
    ].sum(axis=1)

    ordered_bases = [macro_total_base()] + broad_bases + [macro_total_base(True)] + supported_bases
    out = add_rates(out, ordered_bases)

    ordered_cols = list(BASE_TEXT_COLUMNS)
    for base in [macro_total_base()] + broad_bases:
        ordered_cols += [
            f"{base}_raw",
            f"{base}_per_1000",
            f"{base}_per_eligible_paragraph_start",
        ]
    for base in [macro_total_base(True)] + supported_bases:
        ordered_cols += [
            f"{base}_raw",
            f"{base}_per_1000",
            f"{base}_per_eligible_paragraph_start",
        ]
    return out[ordered_cols]


def build_subcategory_indices(eligible_texts, cases):
    base_df = eligible_texts[BASE_TEXT_COLUMNS].copy()
    dictionary_bases = dictionary_subcategory_bases()
    observed_bases = list(dict.fromkeys(cases["subcategory_base"].dropna()))
    broad_bases = dictionary_bases + [base for base in observed_bases if base not in dictionary_bases]
    supported_bases = [f"supported_{base}" for base in broad_bases]

    broad_wide = wide_counts(cases, "subcategory_base", broad_bases)
    supported_cases = cases.copy()
    supported_cases["supported_subcategory_base"] = "supported_" + supported_cases["subcategory_base"]
    supported_wide = wide_counts(
        supported_cases,
        "supported_subcategory_base",
        supported_bases,
        supported=True,
    )

    out = merge_count_wide(base_df, broad_wide)
    out = merge_count_wide(out, supported_wide)
    out = add_rates(out, broad_bases + supported_bases)

    ordered_cols = list(BASE_TEXT_COLUMNS)
    for base in broad_bases + supported_bases:
        ordered_cols += [
            f"{base}_raw",
            f"{base}_per_1000",
            f"{base}_per_eligible_paragraph_start",
        ]
    return out[ordered_cols]


def build_cases_evidence(cases):
    evidence = cases.copy()
    for col in CASE_EVIDENCE_COLUMNS:
        if col not in evidence.columns:
            evidence[col] = pd.NA
    return evidence[CASE_EVIDENCE_COLUMNS]


def build_connector_indices(eligible_texts, cases, macro, dictionary_bases_by_macro):
    base_df = eligible_texts[BASE_TEXT_COLUMNS].copy()
    macro_cases = cases[cases["macro_clean"] == macro].copy()
    dictionary_bases = dictionary_bases_by_macro[macro]
    observed_bases = list(dict.fromkeys(macro_cases["connector_base"].dropna()))
    broad_bases = dictionary_bases + [base for base in observed_bases if base not in dictionary_bases]
    supported_bases = [f"supported_{base}" for base in broad_bases]

    broad_wide = wide_counts(macro_cases, "connector_base", broad_bases)
    supported_cases = macro_cases.copy()
    supported_cases["supported_connector_base"] = "supported_" + supported_cases["connector_base"]
    supported_wide = wide_counts(
        supported_cases,
        "supported_connector_base",
        supported_bases,
        supported=True,
    )

    out = merge_count_wide(base_df, broad_wide)
    out = merge_count_wide(out, supported_wide)
    out = add_rates(out, broad_bases + supported_bases)

    ordered_cols = list(BASE_TEXT_COLUMNS)
    for base in broad_bases + supported_bases:
        ordered_cols += [
            f"{base}_raw",
            f"{base}_per_1000",
            f"{base}_per_eligible_paragraph_start",
        ]
    return out[ordered_cols]


def write_excel(df, path, sheet_name):
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.sheets[sheet_name].freeze_panes = "A2"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ADVANCED_DIR.mkdir(parents=True, exist_ok=True)

    cases, text_indices = load_inputs()
    cases = add_case_bases(cases)

    all_texts = build_all_text_metadata()
    eligible_texts = all_texts[all_texts["eligible_for_interparagraph"]].copy()

    diagnostics = build_diagnostics(all_texts, cases, text_indices)
    macro_indices = build_macro_indices(eligible_texts, cases)
    subcategory_indices = build_subcategory_indices(eligible_texts, cases)
    cases_evidence = build_cases_evidence(cases)

    connector_bases_by_macro = dictionary_connector_bases_by_macro()
    connector_outputs = {
        macro: build_connector_indices(
            eligible_texts,
            cases,
            macro,
            connector_bases_by_macro,
        )
        for macro in MACROS
    }

    write_excel(diagnostics, DIAGNOSTICS_FILE, "Diagnostics")
    write_excel(macro_indices, MACRO_FILE, "Macro indices")
    write_excel(subcategory_indices, SUBCATEGORY_FILE, "Subcategory indices")
    write_excel(cases_evidence, CASES_EVIDENCE_FILE, "Cases evidence")
    for macro, df in connector_outputs.items():
        write_excel(df, CONNECTOR_FILES[macro], f"{macro} connectors")

    output_columns = {
        DIAGNOSTICS_FILE: len(diagnostics.columns),
        MACRO_FILE: len(macro_indices.columns),
        SUBCATEGORY_FILE: len(subcategory_indices.columns),
        CASES_EVIDENCE_FILE: len(cases_evidence.columns),
    }
    output_columns.update({
        CONNECTOR_FILES[macro]: len(df.columns)
        for macro, df in connector_outputs.items()
    })

    print("Built inter-paragraph outcome package")
    print("Eligible texts:", len(eligible_texts))
    print("Case rows:", len(cases))
    print("\nOutput files:")
    for path, n_cols in output_columns.items():
        print(f"- {path}: {n_cols} columns")


if __name__ == "__main__":
    main()
