# Data availability

This repository supports the reproducibility of the conjunction-analysis study by providing code, dictionaries, documentation, synthetic examples, sample outputs, text-level numeric indices, aggregated statistical outputs, and exploratory predictive-analysis outputs.

## Corpus data

The original corpora are not redistributed in this repository because of licensing, copyright, and privacy restrictions.

This repository does not include:
- original COREFL texts
- original EFCAMDAT texts
- original GiG texts
- full sentences or paragraphs extracted from the corpora
- learner identifiers
- sensitive learner metadata
- raw text columns such as `text_raw`, `text_clean_preserveCase`, or `text_clean_lowercase`

Researchers who wish to fully rerun the corpus-level analyses should obtain authorized access to the original corpora from their respective providers.

## Included data

The repository includes safe derived outputs, including:
- text-level numeric conjunction indices
- item-level and macro-category summaries
- dictionary-audit files
- validation documentation
- inferential statistical outputs
- exploratory predictive modelling outputs
- synthetic sample texts and sample outputs

These files are included to make the index-generation and analysis workflow transparent and auditable without redistributing restricted corpus content.

## Synthetic examples

The sample texts included in `samples/` are synthetic and were created only for reproducibility testing. They are not taken from any of the corpora used in the study.
