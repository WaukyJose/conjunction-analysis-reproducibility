# Manual precision-style conjunction audit sample

This file supports a limited diagnostic audit of detected conjunction cases only.
It estimates precision-style reliability for detections, position assignment,
and functional classification. It does not estimate recall because non-detected
conjunctions are not sampled.

## Sampling design

- Target sample: up to 100 detected cases per discourse level.
- Random seed: 42.
- Context export mode: `truncated`.
- Supported-only detections: `True`.
- Intra-sentential precedence alignment: corrected display labels are used for paratactic `and`, `but`, and `or` where applicable; original labels are retained in `original_*` columns.
- Discourse levels: intra-sentential, inter-sentential, inter-paragraph.

## Source files

### intra_sentential
- Source: `outputs/v2_intrasentential_full/v2_intrasentential_full_cases.csv`
- Rows in source: 1173715
- Rows after supported filter: 467879
- Sampled rows: 100
- Support column: `is_priming_supported`
- Rows with intra-sentential precedence display alignment: 43

### inter_sentential
- Source: `outputs/v2_intersentential_full/v2_intersentential_full_cases.csv`
- Rows in source: 193946
- Rows after supported filter: 187675
- Sampled rows: 100
- Support column: `is_intersentential_supported`
- Rows with intra-sentential precedence display alignment: 0

### inter_paragraph
- Source: `outputs/v2_interparagraph_full/v2_interparagraph_full_cases.csv`
- Rows in source: 2248
- Rows after supported filter: 2236
- Sampled rows: 100
- Support column: `is_interparagraph_supported`
- Rows with intra-sentential precedence display alignment: 0

## Manual annotation columns

- `is_conjunction_use`: code `1` if the detected item is a conjunction use in context, otherwise `0`.
- `position_correct`: code `1` if the discourse-position assignment is acceptable, otherwise `0`.
- `function_acceptable`: code `1` if the Hallidayan macro/subcategory assignment is acceptable, otherwise `0`.
- `main_error_type`: use one of `false_positive`, `wrong_position`, `wrong_function`, `ambiguous`, or `other`.
- `notes`: optional short comment.

For strict functional precision, the summary script counts a case as correct only when
`is_conjunction_use`, `position_correct`, and `function_acceptable` are all coded `1`.

## Privacy note

The default sample uses truncated context windows rather than full learner texts.
For public redistribution, review the context fields and remove or further truncate
them if required by corpus licensing or privacy rules.
