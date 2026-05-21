# Index Descriptions

This document explains the main index families produced by ConjuncTool V2. The indices are based on Halliday-oriented categories of conjunction and discourse relation: Extension, Elaboration, and Enhancement.

Output files are saved as CSV files in `/outputs`. Some summary files may report counts by item, macro category, taxis, or text.

## Core Categories

### Extension

Extension indices capture additive, adversative, alternative, replacive, subtractive, and related extending relations. Examples may include markers such as `and`, `but`, `or`, `however`, `moreover`, or related forms, depending on the analysis mode and dictionary level.

### Elaboration

Elaboration indices capture relations that restate, exemplify, clarify, specify, summarise, or verify information. Examples may include markers such as `for example`, `in other words`, `in conclusion`, `indeed`, or related forms.

### Enhancement

Enhancement indices capture temporal, causal, conditional, concessive, comparative, manner, spatial, or matter-related relations. Examples may include markers such as `because`, `if`, `when`, `although`, `therefore`, or related forms.

## Intra-Sentential Indices

Intra-sentential indices describe conjunctions detected within sentence boundaries.

Two output families are available:

- Broad / exploratory intra-sentential indices.
- Supported / validated intra-sentential indices.

The broad output is intentionally inclusive and may contain phrase-level coordination or multifunctional forms. It is useful for exploration but should not be treated as a fully validated clause-linking measure.

The supported output applies stricter lexical-priming and contextual decisions. It is the preferred intra-sentential output for interpretation.

Intra-sentential files may include taxis distinctions:

- Paratactic: coordination-like relations.
- Hypotactic: subordination-like relations.

Common intra-sentential measures include:

- Raw counts.
- Counts per 1,000 words.
- Summaries by macro category.
- Summaries by taxis.
- Summaries by connector item.

## Inter-Sentential Indices

Inter-sentential indices describe sentence-initial discourse markers. These indices count markers that occur at the start of a sentence after a previous sentence.

They are intended to represent discourse organisation between sentences. They are not designed to count every conjunction inside a sentence.

Common inter-sentential measures include:

- Raw counts.
- Counts per 1,000 words.
- Counts or rates by macro category.
- Counts or rates by connector item.

## Inter-Paragraph Indices

Inter-paragraph indices describe paragraph-initial discourse markers. These indices require real paragraph breaks in the input text.

They are intended to represent discourse organisation between paragraphs. If paragraph boundaries are not preserved in the input file, inter-paragraph analysis may not be appropriate.

Common inter-paragraph measures include:

- Raw counts.
- Counts per 1,000 words.
- Counts or rates by macro category.
- Counts or rates by connector item.

## Broad and Supported Outputs

Some modes distinguish broad and supported outputs.

Broad output includes all detected cases after the mode-specific detection rules are applied. It is useful for exploratory analysis and for reviewing possible markers.

Supported output is a stricter subset intended for interpretation. In intra-sentential analysis, supported output reflects lexical-priming and contextual decisions. In sentence-initial and paragraph-initial analyses, supported output reflects marker-confidence and operational filtering.

When both broad and supported outputs are available, supported outputs should usually be used for substantive interpretation.

## Count Types

### Raw Counts

Raw counts report the number of detected markers in a text or category.

### Per-1,000-Word Rates

Per-1,000-word rates normalise raw counts by text length:

`raw count / total words * 1000`

These rates allow comparison across texts of different lengths.

### Text-Level Summaries

Text-level summaries contain one row per analysed text. They are appropriate for statistical modelling, group comparisons, or correlation with other text-level variables.

### Case-Level Evidence

Case-level files contain one row per detected marker. These files are useful for validation, qualitative inspection, and checking how a specific marker was classified.

## Recommended Interpretation

Use the index family that matches the linguistic level of the research question:

- Use intra-sentential supported indices for stricter within-sentence conjunction analysis.
- Use inter-sentential indices for sentence-initial discourse organisation.
- Use inter-paragraph indices for paragraph-initial discourse organisation when paragraph breaks are preserved.

Researchers should inspect case-level evidence for important analyses, especially when working with highly multifunctional connectors or texts with unusual formatting.
