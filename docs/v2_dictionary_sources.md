# V2 dictionary sources

These dictionary files were copied into `Conjunction_Research_V2/resources/` for Parser V2 development.

## Files

| File | Size | Modified | SHA-256 |
|---|---:|---|---|
| `resources/halliday_intrasent_dic.py` | 3,745 | 2026-04-29 14:57:48 | `471ec4de3f8e902a7f83417920204d4e4f849288b3bb0f6381fa484a954518cb` |
| `resources/halliday_intersent_dic.py` | 15,268 | 2026-04-29 14:57:48 | `26ba6a632c3cf10831198b9ce021a195c55872155ecd5a06391f5f9878b39682` |
| `resources/halliday_paragraph_dict.py` | 52,360 | 2026-04-29 15:04:07 | `af3b4d04b7a72464fbdbf6573e0d3f09710d11f1566bd04a6eb06aa81b07fdd8` |

## Purpose

These files define the Halliday-based conjunction inventories used for V2 parser development.

## Caution

Before final analysis, these dictionaries must be checked against the latest manuscript terminology and index names to avoid analysing an outdated dictionary version.

## Dictionary structure audit

A recursive dictionary audit showed:

| Level | Raw index structures | Macro breakdown |
|---|---:|---|
| Intra-sentential | 33 | Elaboration = 6; Extension = 8; Enhancement = 19 |
| Inter-sentential | 38 | Elaboration = 9; Extension = 6; Enhancement = 23 |
| Inter-paragraph | 39 | Elaboration = 9; Extension = 7; Enhancement = 23 |

The inter-paragraph dictionary includes one extra Extension category: `Stance_Markers`.

For V2 main analysis, `Stance_Markers` will be excluded from the core paragraph-level index set so that the inter-paragraph indices match the manuscript Table 3 structure:

Elaboration = 9; Extension = 6; Enhancement = 23; Total = 38.

Stance markers may be retained only as an optional exploratory diagnostic feature, not as part of the main Halliday expansion index set.
