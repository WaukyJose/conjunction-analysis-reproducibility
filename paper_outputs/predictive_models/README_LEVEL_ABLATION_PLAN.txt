Exploratory predictive analysis: level-ablation plan

Purpose:
The level-ablation analysis will examine where the developmental signal is located in the position-sensitive conjunction indices.

Main question:
Do intra-sentential, inter-sentential, or inter-paragraph indices provide stronger information for distinguishing developmental groupings?

This analysis is exploratory. It is not intended to make causal claims about writing development.

Unit of analysis:
One text = one observation.

Targets:
- COREFL: CEFR level
- EFCAMDAT: CEFR/EF level
- GiG: school year

Models for COREFL:
1. intra-sentential indices only
2. inter-sentential indices only
3. inter-paragraph indices only
4. all three levels combined

Models for GiG:
1. intra-sentential indices only
2. inter-sentential indices only
3. inter-paragraph indices only
4. all three levels combined

Models for EFCAMDAT:
1. intra-sentential indices only
2. inter-sentential indices only
3. all available levels combined

EFCAMDAT does not include an inter-paragraph model because paragraph boundaries were not treated as reliable for that corpus.

Predictors:
Only normalized *_per_1000 indices will be used. Raw count features will be excluded to reduce text-length confounding.

Evaluation:
Each Random Forest model will be compared with a most-frequent-class baseline.

Main metric:
macro-F1

Additional metrics:
- balanced accuracy
- accuracy

Interpretation rule:
The results will be interpreted as evidence of which discourse level is more informative for classification, not as evidence that a level causes developmental differences.

Next computational step:
Run baseline + Random Forest models for each corpus and each discourse-level feature set.
