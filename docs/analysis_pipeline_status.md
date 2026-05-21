# Analysis Pipeline Status

## Current status

Preprocessing is complete.

Final analytic datasets:

| Corpus   | Final analytic n | Threshold |
|----------|-----------------:|----------:|
| COREFL   | 3,416            | ≥50 words |
| EFCAMDAT | 232,565          | ≥50 words |
| GiG      | 2,684            | ≥50 words |

## Next step

Regenerate all text-level conjunction index outputs from the final analytic datasets before rerunning any statistics.

Required regeneration:

1. Intra-sentential indices
2. Inter-sentential indices
3. Inter-paragraph indices
4. Zero-density rows preserved

## After regeneration

Rerun:

1. Descriptive statistics
2. Kruskal-Wallis tests
3. Dunn posthoc tests
4. Spearman correlations
5. Modelling analyses

## Important rule

Do not rerun preprocessing audits unless a clear reproducible error is found.
