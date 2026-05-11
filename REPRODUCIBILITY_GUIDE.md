# Reproducibility guide

This repository provides the materials needed to inspect and reproduce the conjunction-index workflow used in the study.

## 1. Install requirements

From the repository root, run:

pip install -r requirements.txt

## 2. Run ConjuncTool on synthetic examples

Launch the graphical interface:

python launch_gui.py

Use the synthetic files in the samples folder:

- synthetic_intra_text.txt: intra-sentential supported analysis
- synthetic_intersent_text.txt: inter-sentential analysis
- synthetic_interpara_text.txt: inter-paragraph analysis

Example outputs are available in the sample_outputs folder.

## 3. Inspect dictionaries

The Halliday-based conjunction dictionaries are stored in app/dictionaries.

Dictionary-audit files are stored in dictionary_audit.

## 4. Inspect paper outputs

Safe derived outputs are stored in paper_outputs, including:

- text_level_indices
- summary_outputs
- inferential_statistics
- predictive_models

These files support the descriptive, inferential, and exploratory predictive analyses reported in the paper.

## 5. Corpus-level reruns

The original corpora are not included in this repository. To fully rerun the corpus-level analyses, researchers must obtain authorized access to COREFL, EFCAMDAT, and GiG, then apply the same parser and index-generation workflow.

## 6. Privacy and licensing

Files containing original corpus texts, full sentences, paragraphs, learner identifiers, or sensitive metadata are not redistributed.
