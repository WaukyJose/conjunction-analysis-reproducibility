# ConjuncTool V2 User Guide

ConjuncTool V2 is a Tkinter application for Halliday-based conjunction analysis. It identifies conjunctions and discourse markers across intra-sentential, inter-sentential, and inter-paragraph environments, and exports CSV summaries for further analysis.

The tool is designed for research use. It can analyse any plain-text `.txt` file supplied by the user. The files in `/samples` are provided only for testing installation and confirming that the interface runs correctly.

## Analysis Modes

The graphical interface provides four analysis modes.

### 1. Intra-Sentential — Broad / Exploratory

This mode detects conjunctions within sentence boundaries. It is intentionally broad and is useful for exploratory analysis, dictionary auditing, and inspecting possible coordination or subordination patterns.

Because it is broad, this output may include phrase-level coordination and other multifunctional forms. For example, common items such as `and`, `or`, `as`, `while`, and `but` can serve several grammatical or discourse functions depending on context. Broad intra-sentential results should therefore be interpreted cautiously.

### 2. Intra-Sentential — Supported / Validated

This mode provides a stricter intra-sentential subset. It applies lexical-priming and contextual support decisions to reduce ambiguous or low-confidence cases.

For interpretation, reporting, or comparison across texts, the supported intra-sentential output should normally be preferred over the broad exploratory output.

### 3. Inter-Sentential — Validated

This mode detects sentence-initial discourse markers. It analyses markers that occur at the beginning of a sentence after a previous sentence, such as sentence-initial additive, adversative, elaborative, causal, conditional, or temporal markers.

Inter-sentential analysis is intended to capture relations between sentences rather than conjunctions inside a single sentence.

### 4. Inter-Paragraph — Validated

This mode detects paragraph-initial discourse markers. It requires real paragraph breaks in the input text, because paragraph boundaries are central to the analysis.

If a text does not contain preserved paragraph breaks, it may not be eligible for inter-paragraph analysis. Users should ensure that paragraphs are separated by line breaks in the `.txt` file.

## Input Files

Users may analyse any `.txt` file. The text should be plain text, encoded in a standard format such as UTF-8.

For best results:

- Use one complete text per file.
- Preserve paragraph breaks if running inter-paragraph analysis.
- Avoid manually inserting artificial line breaks inside sentences unless they are real paragraph boundaries.
- Check that the file contains readable text before analysis.

The `/samples` directory is for installation testing only. Sample files are not required for analysis and should not be treated as the only valid input format.

## Output Files

ConjuncTool V2 saves output CSV files in `/outputs`.

Depending on the selected mode, outputs may include:

- Case-level files, with one row per detected marker.
- Text-level summary files, with one row per analysed text.
- Summary files by item.
- Summary files by macro category.
- Summary files by taxis, where relevant.

CSV files can be opened in spreadsheet software or imported into statistical software such as R, Python, SPSS, Stata, or Jamovi.

## Interpreting Results

The tool follows Halliday-based categories including Extension, Elaboration, and Enhancement. In intra-sentential analysis, taxis distinctions such as paratactic and hypotactic may also be reported.

Raw counts show how many markers were detected. Normalised rates, where provided, express counts relative to text length, usually per 1,000 words.

Users should distinguish between broad and supported outputs:

- Broad intra-sentential results are exploratory.
- Supported intra-sentential results are stricter and better suited for interpretation.
- Inter-sentential and inter-paragraph modes are validated sentence-initial and paragraph-initial analyses.

All automated annotation should be interpreted in relation to the research question, text type, and quality of the input text.

## Recommended Workflow

1. Prepare plain-text `.txt` files.
2. Run a sample file from `/samples` only to confirm that installation works.
3. Select the analysis mode appropriate to the research question.
4. Run the analysis on the target `.txt` file.
5. Review the generated CSV files in `/outputs`.
6. Use supported or validated outputs for interpretation whenever available.

## Notes on Scope

ConjuncTool V2 is a rule-based corpus analysis tool. It does not replace close linguistic analysis. Its outputs are best used as systematic indicators of conjunction and discourse-marker use, supported by inspection of examples where needed.
