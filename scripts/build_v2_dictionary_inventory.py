from pathlib import Path
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RESOURCES_DIR = BASE_DIR / "resources"
OUT_DIR = BASE_DIR / "outputs" / "dictionary_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(RESOURCES_DIR))

from halliday_intrasent_dic import INTRA_CLAUSE_CONJUNCTIONS
from halliday_intersent_dic import HALLIDAY_CONJUNCTIONS as INTERSENT_CONJUNCTIONS
from halliday_paragraph_dict import HALLIDAY_CONJUNCTIONS as PARAGRAPH_CONJUNCTIONS


def recursive_flatten(obj, level_name, path=None):
    if path is None:
        path = []

    rows = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            rows.extend(recursive_flatten(value, level_name, path + [key]))

    elif isinstance(obj, list):
        for connector in obj:
            row = {
                "level": level_name,
                "connector": str(connector).strip(),
            }

            for i, part in enumerate(path, start=1):
                row[f"path_{i}"] = part

            rows.append(row)

    return rows


def build_inventory():
    all_rows = []

    dictionaries = {
        "intra_sentential": INTRA_CLAUSE_CONJUNCTIONS,
        "inter_sentential": INTERSENT_CONJUNCTIONS,
        "inter_paragraph": PARAGRAPH_CONJUNCTIONS,
    }

    for level_name, dictionary in dictionaries.items():
        all_rows.extend(recursive_flatten(dictionary, level_name))

    df = pd.DataFrame(all_rows)

    # Standardise path columns
    for col in ["path_1", "path_2", "path_3", "path_4", "path_5"]:
        if col not in df.columns:
            df[col] = ""

    df["macro_category"] = df["path_1"].fillna("")
    df["connector_lower"] = df["connector"].str.lower().str.strip()

    # Exclude paragraph stance markers from MAIN index inventory
    df["include_main_v2"] = True
    df.loc[
        (df["level"] == "inter_paragraph")
        & (df["path_1"] == "Extension")
        & (df["path_2"] == "Stance_Markers"),
        "include_main_v2"
    ] = False

    return df


def build_index_counts(df):
    path_cols = ["path_1", "path_2", "path_3", "path_4", "path_5"]

    rows = []

    for level_name, level_df in df.groupby("level"):
        for scope_name, scope_df in [
            ("all_dictionary_entries", level_df),
            ("main_v2_included_only", level_df[level_df["include_main_v2"]]),
        ]:
            index_df = scope_df[path_cols].drop_duplicates()

            by_macro = (
                index_df.groupby("path_1")
                .size()
                .reset_index(name="n_indices")
                .rename(columns={"path_1": "macro_category"})
            )

            for _, row in by_macro.iterrows():
                rows.append({
                    "level": level_name,
                    "scope": scope_name,
                    "macro_category": row["macro_category"],
                    "n_indices": row["n_indices"],
                })

            rows.append({
                "level": level_name,
                "scope": scope_name,
                "macro_category": "TOTAL",
                "n_indices": len(index_df),
            })

    return pd.DataFrame(rows)


def main():
    inventory = build_inventory()
    counts = build_index_counts(inventory)

    inventory_path = OUT_DIR / "v2_recursive_dictionary_inventory.csv"
    counts_path = OUT_DIR / "v2_recursive_index_counts.csv"

    inventory.to_csv(inventory_path, index=False)
    counts.to_csv(counts_path, index=False)

    print("Wrote:", inventory_path)
    print("Wrote:", counts_path)

    print("\nMAIN V2 INDEX COUNTS")
    print(
        counts[counts["scope"] == "main_v2_included_only"]
        .sort_values(["level", "macro_category"])
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()