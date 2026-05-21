from pathlib import Path
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RESOURCES = BASE_DIR / "resources"
OUT_DIR = BASE_DIR / "outputs" / "dictionary_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(RESOURCES))

from halliday_intrasent_dic import INTRA_CLAUSE_CONJUNCTIONS
from halliday_intersent_dic import HALLIDAY_CONJUNCTIONS as INTERSENT_CONJUNCTIONS
from halliday_paragraph_dict import HALLIDAY_CONJUNCTIONS as PARAGRAPH_CONJUNCTIONS


def flatten_intra():
    rows = []
    for macro, subdict in INTRA_CLAUSE_CONJUNCTIONS.items():
        for subcategory, subsubdict in subdict.items():
            if isinstance(subsubdict, dict):
                for relation, taxis_dict in subsubdict.items():
                    if isinstance(taxis_dict, dict):
                        for taxis, items in taxis_dict.items():
                            for item in items:
                                rows.append({
                                    "level": "intra_sentential",
                                    "macro_category": macro,
                                    "subcategory": subcategory,
                                    "relation": relation,
                                    "taxis": taxis,
                                    "connector": item,
                                })
                    elif isinstance(taxis_dict, list):
                        for item in taxis_dict:
                            rows.append({
                                "level": "intra_sentential",
                                "macro_category": macro,
                                "subcategory": subcategory,
                                "relation": relation,
                                "taxis": "",
                                "connector": item,
                            })
    return pd.DataFrame(rows)


def flatten_inter_or_para(dictionary, level_name):
    rows = []
    for macro, subdict in dictionary.items():
        for subcategory, items in subdict.items():
            if isinstance(items, dict):
                for relation, connectors in items.items():
                    if isinstance(connectors, list):
                        for item in connectors:
                            rows.append({
                                "level": level_name,
                                "macro_category": macro,
                                "subcategory": subcategory,
                                "relation": relation,
                                "taxis": "",
                                "connector": item,
                            })
            elif isinstance(items, list):
                for item in items:
                    rows.append({
                        "level": level_name,
                        "macro_category": macro,
                        "subcategory": subcategory,
                        "relation": "",
                        "taxis": "",
                        "connector": item,
                    })
    return pd.DataFrame(rows)


def summarise(df, level_name):
    return {
        "level": level_name,
        "n_rows": len(df),
        "n_unique_connectors": df["connector"].str.lower().nunique(),
        "n_macro_categories": df["macro_category"].nunique(),
        "macro_categories": "; ".join(sorted(df["macro_category"].dropna().unique())),
        "n_subcategories": df["subcategory"].nunique(),
        "n_relations": df["relation"].replace("", pd.NA).dropna().nunique(),
        "n_taxis_values": df["taxis"].replace("", pd.NA).dropna().nunique(),
        "taxis_values": "; ".join(sorted(df["taxis"].replace("", pd.NA).dropna().unique())),
    }


def duplicate_report(df, level_name):
    tmp = df.copy()
    tmp["connector_lower"] = tmp["connector"].str.lower().str.strip()
    dup = (
        tmp.groupby("connector_lower")
        .agg(
            n_entries=("connector", "size"),
            macro_categories=("macro_category", lambda x: "; ".join(sorted(set(x)))),
            subcategories=("subcategory", lambda x: "; ".join(sorted(set(x)))),
            relations=("relation", lambda x: "; ".join(sorted(set([v for v in x if v])))),
            taxis_values=("taxis", lambda x: "; ".join(sorted(set([v for v in x if v])))),
        )
        .reset_index()
    )
    dup = dup[dup["n_entries"] > 1].sort_values(["n_entries", "connector_lower"], ascending=[False, True])
    dup.insert(0, "level", level_name)
    return dup


def main():
    intra = flatten_intra()
    inter = flatten_inter_or_para(INTERSENT_CONJUNCTIONS, "inter_sentential")
    para = flatten_inter_or_para(PARAGRAPH_CONJUNCTIONS, "inter_paragraph")

    intra.to_csv(OUT_DIR / "intra_dictionary_inventory.csv", index=False)
    inter.to_csv(OUT_DIR / "intersent_dictionary_inventory.csv", index=False)
    para.to_csv(OUT_DIR / "paragraph_dictionary_inventory.csv", index=False)

    summary = pd.DataFrame([
        summarise(intra, "intra_sentential"),
        summarise(inter, "inter_sentential"),
        summarise(para, "inter_paragraph"),
    ])
    summary.to_csv(OUT_DIR / "dictionary_index_counts.csv", index=False)

    duplicates = pd.concat([
        duplicate_report(intra, "intra_sentential"),
        duplicate_report(inter, "inter_sentential"),
        duplicate_report(para, "inter_paragraph"),
    ], ignore_index=True)
    duplicates.to_csv(OUT_DIR / "dictionary_duplicate_connectors.csv", index=False)

    print("\nDictionary audit written to:", OUT_DIR)
    print("\nSUMMARY")
    print(summary.to_string(index=False))

    print("\nTop duplicate connectors")
    if duplicates.empty:
        print("No duplicate connector entries found.")
    else:
        print(duplicates.head(30).to_string(index=False))


if __name__ == "__main__":
    main()