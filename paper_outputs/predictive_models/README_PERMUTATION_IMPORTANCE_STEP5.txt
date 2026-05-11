Exploratory predictive analysis: permutation importance

Purpose:
Permutation importance was calculated for the all-available Random Forest models to examine which position-sensitive conjunction indices were most informative within each corpus-specific model.

Important design point:
The Random Forest models were trained separately by corpus. Therefore, the merged ranked table should be interpreted as an exploratory comparative overview, not as a single pooled model across corpora.

Outputs:
- corefl_all_available_permutation_importance.csv
- efcamdat_all_available_permutation_importance.csv
- gig_all_available_permutation_importance.csv
- merged_ordered_permutation_importance_all_corpora.csv
- top30_ordered_predictors_all_corpora.csv
- importance_summary_by_corpus_and_discourse_level.csv

Main observations:
- GiG showed the clearest support for paragraph-level discourse signal: inter-paragraph features had the highest total importance.
- EFCAMDAT showed similar total importance for inter-sentential and intra-sentential features; inter-paragraph features were not available.
- COREFL feature rankings should be interpreted cautiously because the COREFL classification model showed weak overall performance.

Interpretation rule:
Permutation importance is interpreted as predictive informativeness within the corpus-specific model, not as causal evidence of writing development.
