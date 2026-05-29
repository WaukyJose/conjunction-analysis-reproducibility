# Manual precision-style audit summary

- Input file: `validation/manual_precision_audit_annotated_cleaned.csv`
- Scope: detected conjunction cases only.
- Recall is not estimated.

## Precision summaries

| discourse_level   |   sampled_rows |   annotated_is_conjunction_use_n |   annotated_position_correct_n |   annotated_function_acceptable_n |   fully_annotated_n |   detection_precision |   position_precision |   strict_functional_precision |
|:------------------|---------------:|---------------------------------:|-------------------------------:|----------------------------------:|--------------------:|----------------------:|---------------------:|------------------------------:|
| inter_paragraph   |            100 |                              100 |                            100 |                               100 |                 100 |                 1.000 |                0.990 |                         0.950 |
| inter_sentential  |            100 |                              100 |                            100 |                               100 |                 100 |                 1.000 |                1.000 |                         0.940 |
| intra_sentential  |            100 |                               99 |                            100 |                               100 |                  99 |                 0.818 |                0.780 |                         0.778 |
| overall           |            300 |                              299 |                            300 |                               300 |                 299 |                 0.940 |                0.923 |                         0.890 |

## Error-type counts

| discourse_level   | main_error_type   |   count |
|:------------------|:------------------|--------:|
| inter_paragraph   | wrong_function    |       4 |
| inter_paragraph   | wrong_position    |       1 |
| inter_sentential  | wrong_function    |       6 |
| intra_sentential  | false_positive    |      19 |
| intra_sentential  | wrong_position    |       3 |

## Metric definitions

- `detection_precision`: mean of `is_conjunction_use`.
- `position_precision`: mean of `position_correct`.
- `strict_functional_precision`: mean of cases where `is_conjunction_use`, `position_correct`, and `function_acceptable` are all `1`.

## Annotation completeness

Rows with blank annotation cells are excluded from the relevant mean.
