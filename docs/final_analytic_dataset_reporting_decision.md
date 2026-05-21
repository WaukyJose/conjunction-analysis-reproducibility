# Decision Note: Final Analytic Dataset Reporting and Preprocessing Closure

## Date
2026-05-21

## Purpose

This note documents the final reporting decision for the analytic datasets used in the study.

The manuscript will report only the **final analytic datasets** used for index generation, inferential statistics, descriptive analysis, correlation analysis, and modelling.

The central reporting principle is:

> Report the data that entered the analyses.

This avoids confusion caused by intermediate preprocessing files, earlier audit versions, malformed-row checks, raw corpus sizes, or temporary exported datasets.

---

## Final analytic datasets

The final analytic datasets are:

| Corpus   | Final analytic n | Threshold |
|----------|-----------------:|----------:|
| COREFL   | 3,416            | ≥50 words |
| EFCAMDAT | 232,565          | ≥50 words |
| GiG      | 2,684            | ≥50 words |

All three corpora are now filtered using the same minimum text-length criterion:

\[
\text{all corpora} \geq 50 \text{ words}
\]

This creates a unified discourse-eligibility threshold across the study.

---

## Final preprocessing status

The preprocessing phase is now considered complete.

The final analytic datasets contain:

- no malformed rows,
- no empty texts,
- no duplicate IDs,
- no missing group labels,
- no ultra-short texts below the 50-word threshold.

No further dataset-audit cycles should be conducted unless a clear, reproducible error is discovered.

Further auditing at this stage may create unnecessary version confusion and increase the risk of contradictory corpus-size reporting.

---

## Methodological rationale

Applying the same ≥50-word threshold across COREFL, EFCAMDAT, and GiG strengthens the methodological design by reducing:

- denominator instability,
- ultra-short discourse artefacts,
- threshold asymmetry across corpora,
- reviewer concerns about inconsistent filtering,
- and normalization-related criticism.

This is especially important because the study analyses conjunction use across discourse positions. Very short texts provide limited opportunities for sentence-level and paragraph-level cohesion, so excluding ultra-short texts improves the interpretability of normalized conjunction indices.

---

## Manuscript reporting rule

The paper should report only the final analytic Ns:

| Corpus   | N texts |
|----------|--------:|
| COREFL   | 3,416   |
| EFCAMDAT | 232,565 |
| GiG      | 2,684   |

The manuscript should avoid foregrounding:

- raw source corpus sizes,
- cleaned-but-unfiltered corpus sizes,
- malformed-row counts,
- early audit versions,
- temporary preprocessing exports,
- or previous COREFL counts.

Raw corpus sizes may be mentioned briefly only if historically relevant in corpus descriptions, but all statistical tables, figures, captions, and inferential claims should use the final analytic Ns above.

---

## Recommended manuscript wording

Table 2 reports the final analytic corpus sizes used in the study after preprocessing, metadata alignment, and analytic filtering. All three corpora were restricted to texts containing at least 50 words. The final analytic datasets contained no malformed rows, empty texts, duplicate IDs, missing group labels, or ultra-short texts below the 50-word threshold. Additional structural filtering was applied only for analyses requiring paragraph boundaries, where texts without reliable paragraph segmentation were excluded from inter-paragraph calculations.

---

## Pipeline status

The preprocessing phase is complete.

The next stage of the pipeline is:

\[
\text{Final analytic datasets}
\rightarrow
\text{Index regeneration}
\rightarrow
\text{Corrected inferential statistics}
\rightarrow
\text{Updated results and discussion}
\]

The next practical step is to regenerate text-level outputs from the definitive analytic datasets.

This should include:

- regenerated intra-sentential outputs,
- regenerated inter-sentential outputs,
- regenerated inter-paragraph outputs,
- preservation of zero-density rows,
- and updated text-level index files.

Only after regenerating the outputs should the following analyses be rerun:

- descriptive statistics,
- Kruskal-Wallis tests,
- Dunn posthoc tests,
- Spearman correlations,
- and modelling procedures.

---

## Specific revision decisions

The manuscript should remove or revise any sentence suggesting that GiG did not receive the same 50-word threshold as the other corpora.

The following claim should not appear in the manuscript:

> No equivalent 50-word threshold was applied to GiG.

This is no longer accurate.

The paper should also avoid using the previous COREFL analytic n of 3,448. The correct final COREFL analytic n is now:

\[
N = 3,416
\]

---

## Final decision

The final analytic foundation of the study is now stable.

No further preprocessing audits are required before index regeneration.

The study should now proceed from these final analytic datasets to regenerated indices and updated statistical analyses.
