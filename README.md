# Conjunction analysis reproducibility package

This repository contains the reproducibility materials for a study of position-sensitive conjunction use across L1 and L2 writing.

The project implements Halliday-based conjunction indices at three discourse levels:

- intra-sentential
- inter-sentential
- inter-paragraph

The repository includes parser code, dictionaries, dictionary-audit files, synthetic examples, sample outputs, validation documentation, safe text-level index outputs, aggregated statistical outputs, and exploratory predictive-analysis outputs.

## Repository structure

- app: ConjuncTool parser code, dictionaries, GUI, and export utilities
- dictionary_audit: dictionary inventories and duplicate-connector audits
- samples: synthetic texts for testing the parser
- sample_outputs: example outputs generated from the synthetic texts
- paper_outputs: safe numeric outputs used in the paper
- validation: validation documentation and templates
- docs: development and method documentation

## Data availability

The original corpora are not redistributed because of licensing, copyright, and privacy restrictions.

This repository does not include original corpus texts, full sentences, paragraphs, learner identifiers, or sensitive metadata.

See DATA_AVAILABILITY.md for details.

## Reproducibility

See REPRODUCIBILITY_GUIDE.md for instructions on installing requirements, running ConjuncTool on the synthetic examples, and inspecting the derived outputs.
