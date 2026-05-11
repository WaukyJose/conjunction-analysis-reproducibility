Exploratory predictive analysis: level-ablation results

Purpose:
The level-ablation analysis examined whether developmental signal varied by discourse level:
- intra-sentential indices only
- inter-sentential indices only
- inter-paragraph indices only, where available
- all available levels combined

Models:
Random Forest classifiers were trained separately by corpus and compared with a most-frequent-class baseline.

Main metric:
macro-F1

Additional metrics:
- balanced accuracy
- accuracy

Feature treatment:
Only normalized *_per_1000 indices were used.
Raw count features were excluded.
Features with no variance after zero-filling were removed before modelling.

Corpus-specific design:
COREFL:
- intra-sentential only
- inter-sentential only
- inter-paragraph only
- all available levels

EFCAMDAT:
- intra-sentential only
- inter-sentential only
- all available levels
- no inter-paragraph model because paragraph boundaries were not treated as reliable

GiG:
- intra-sentential only
- inter-sentential only
- inter-paragraph only
- all available levels

Main results:
COREFL showed weak predictive signal overall. The inter-sentential-only model produced the highest macro-F1 among level-specific models.

EFCAMDAT showed moderate predictive signal. Intra-sentential and inter-sentential models performed similarly, while the all-available model improved macro-F1 and accuracy.

GiG showed the clearest level-ablation pattern. The inter-paragraph-only model outperformed the intra-sentential-only and inter-sentential-only models, and the all-available model performed best overall.

Interpretation rule:
These results should be interpreted as evidence of predictive informativeness, not as causal evidence that a discourse level causes writing development.

Saved output:
level_ablation_random_forest_results.csv
