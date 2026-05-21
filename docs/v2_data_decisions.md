# V2 data decisions

## Data source

V2 starts from the cleaned datasets copied from the original `conjunction_project/data_clean/` folder:

- `efcamdat_clean.csv`
- `ielts_clean.csv`
- `gig_clean.csv`

Raw data are not reprocessed at this stage, because V2 is intended to test parser improvements while keeping the cleaned input layer stable.

## Filtering decision

For V2, texts are filtered using:

`wc_preserve >= 50`

and missing text values are removed.

## Filtered V2 datasets

- `data_filtered/efcamdat_v2_filtered.csv`
- `data_filtered/ielts_v2_filtered.csv`
- `data_filtered/gig_v2_filtered.csv`

## Filter summary

| Corpus | Original rows | Filtered rows | Removed | Removed % |
|---|---:|---:|---:|---:|
| EFCAMDAT | 404,144 | 232,565 | 171,579 | 42.45 |
| IELTS | 9,255 | 9,254 | 1 | 0.01 |
| GiG | 2,898 | 2,684 | 214 | 7.38 |

## Grouping variables for V2

- EFCAMDAT: `cefr`
- IELTS: `band`
- GiG: `year_group`

## Paragraph boundary decision

- GiG preserves newline paragraph structure in most texts and can support true paragraph-level analysis.
- EFCAMDAT and IELTS do not preserve newline paragraph structure in the cleaned files.
- Therefore, V2 should not make strong true inter-paragraph claims for EFCAMDAT or IELTS unless raw paragraph boundaries are recovered later.

## IELTS replacement decision

The Hugging Face IELTS dataset is removed from the main V2 analysis because its provenance and reliability are not strong enough for the final publication workflow.

V2 replaces IELTS with COREFL written learner texts.

COREFL inclusion criteria:

- Subcorpus: Learners
- Medium: Written
- Task title: Film, Chaplin, or Frog
- Minimum text length: 20 words
- Available CEFR proficiency metadata

Filtered COREFL V2 file:

- `data_filtered/corefl_v2_filtered.csv`

Filtered COREFL summary:

- Texts: 3,448
- Levels: A1–C2
- Main L1: Spanish-dominant multilingual learner sample
- Paragraph breaks available in 987 texts

The new V2 main corpus design is:

- EFCAMDAT: L2 writing, CEFR grouped
- COREFL: L2 writing, CEFR grouped
- GiG: L1 school writing, year-group grouped
