# Decision Note: Reporting Final Analytic Datasets

## Datey

2026-05-20

## Purpose

This note documents the reporting decision for corpus sizes and analytic datasets in the manuscript.

The paper will report only the **final analytic datasets** used in the actual analyses, rather than all intermediate preprocessing outputs.

This decision was made to avoid confusion caused by multiple corpus-size values arising from:

- raw source corpus sizes,
- cleaned corpus files,
- malformed-row removal,
- metadata alignment,
- filtering thresholds,
- structural filtering,
- earlier audit versions,
- and intermediate exported files.

The central reporting principle is:

> Report the data that entered the analyses.

## Final analytic datasets

The manuscript should report the following final analytic dataset sizes:

| Corpus        | N Texts | Group variable              | Task / text type                     |
|--------------|--------:|-----------------------------|--------------------------------------|
| COREFL (L2)  | 3,448   | CEFR A1–C2                  | Written narratives                   |
| EFCAMDAT (L2)| 232,565 | EF levels 1–15              | General learner compositions         |
| GiG (L1)     | 2,684   | School Years 2, 4, 6, 9, 11 | Literary/non-literary school writing |

## Recommended manuscript wording

Table 2 reports the final analytic corpus sizes used in the study after preprocessing, metadata alignment, and analytic filtering. EFCAMDAT and GiG were restricted to texts containing at least 50 words, whereas COREFL retained all metadata-aligned texts. Additional structural filtering was applied for inter-paragraph analyses, where only texts with reliable paragraph boundaries were included.

## Reporting rule for the manuscript

The manuscript should avoid reporting multiple competing corpus-size values unless they are strictly necessary.

Therefore, the paper should not foreground:

- raw cleaned corpus sizes,
- intermediate preprocessing files,
- malformed-row counts,
- early-stage audit versions,
- temporary exported files,
- or historical pipeline artefacts.

Raw source corpus sizes may be mentioned briefly in corpus descriptions if needed, but inferential statistics, normalized indices, and modelling results should refer only to the final analytic datasets.

## Specific revision decision

The sentence:

> No equivalent 50-word threshold was applied to GiG...

should be removed because it no longer reflects the final analytic dataset and may create reviewer confusion.

## Rationale

This reporting strategy is cleaner, more reviewer-friendly, and methodologically safer. Reviewers are primarily interested in knowing which data entered the analyses, not every intermediate preprocessing stage.

This decision also reduces the risk of contradictory Ns across the paper and helps stabilize the Methods, Results, tables, and captions.
