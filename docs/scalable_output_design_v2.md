# Scalable Output Design V2

This note documents the planned scalable output design for conjunction index exports in Conjunction Research V2 and the related ConjuncTool application.

The project uses Halliday-based dictionaries and parser-assigned fields such as `macro_category`, `path_2`, `path_3`, `path_4`, `path_5`, `taxis`, and `detected_item`. These fields make it possible to preserve detailed linguistic annotation without forcing every possible conjunction item into a separate text-level spreadsheet column.

## Rationale

The project should not create one wide text-level column for every individual conjunction item. The dictionaries may eventually contain hundreds or more than 1,000 items. A fully wide connector-level spreadsheet would become very large, sparse, slow to open, and difficult to analyse in standard spreadsheet software.

The scalable design separates evidence, compact statistical summaries, and item-level detail:

- Case-level files preserve every detected occurrence.
- Text-level files remain compact and suitable for statistical modelling.
- Long-format item-level files preserve item-specific counts without creating thousands of mostly empty columns.

This design also avoids overclaiming. Grouped indices should aggregate only labels already assigned by the parser. They should not introduce manually invented categories after detection.

## Proposed File Roles

### 1. Case-Level Evidence Files

Pattern:

`*_results.csv`

Role:

These files contain one row per detected case. They preserve exact evidence and should remain the most detailed audit trail.

Expected fields include:

- `text_id`
- `analysis_level`
- `detected_item`
- `macro_category`
- `path_2`
- `path_3`
- `path_4`
- `path_5`
- `taxis`
- context fields, such as sentence, paragraph, or local span
- parser decision fields, where relevant

Case-level files are the correct place to inspect individual detections, validate classifications, and troubleshoot ambiguous forms.

### 2. Main Text-Level Statistical Files

Pattern:

`*_text_indices.csv`

Role:

These files should remain compact and statistical. They should contain one row per text and a controlled number of columns.

They should include:

- total counts and per-1,000-word rates
- macro-category counts and per-1,000-word rates
- taxis counts and per-1,000-word rates where relevant
- grouped functional-path indices based on parser-assigned labels

These files should not include one column per individual conjunction item when the dictionary is large.

Example text-level columns:

- `text_id`
- `word_count_text`
- `intra_total_raw`
- `intra_total_per_1000`
- `intra_extension_raw`
- `intra_extension_per_1000`
- `intra_elaboration_raw`
- `intra_elaboration_per_1000`
- `intra_enhancement_raw`
- `intra_enhancement_per_1000`
- `intra_paratactic_raw`
- `intra_paratactic_per_1000`
- `intra_hypotactic_raw`
- `intra_hypotactic_per_1000`
- `intra_enh_caus_reason_hypo_raw`
- `intra_enh_caus_reason_hypo_per_1000`

### 3. Long-Format Item-Level Files

Pattern:

`*_item_indices.csv`

Role:

These files preserve item-specific statistics without creating a very wide spreadsheet. They should contain one row per detected item type per text.

Required fields:

- `text_id`
- `analysis_level`
- `detected_item`
- `macro_category`
- `path_2`
- `path_3`
- `path_4`
- `path_5`
- `taxis`
- `raw_count`
- `per_1000`
- `word_count_text`

Example rows:

| text_id | analysis_level | detected_item | macro_category | path_2 | path_3 | path_4 | path_5 | taxis | raw_count | per_1000 | word_count_text |
|---|---|---|---|---|---|---|---|---|---:|---:|---:|
| T001 | intra_sentential | because | Enhancement | Causal-Conditional | Reason |  |  | hypotactic | 3 | 6.00 | 500 |
| T001 | intra_sentential | and | Extension | Addition |  |  |  | paratactic | 5 | 10.00 | 500 |

This format is easier to filter, pivot, and aggregate in R, Python, or statistical software.

## Grouped Functional-Path Codes

Grouped functional indices may use short feature codes, but each code must be generated from a controlled abbreviation mapping rather than random truncation.

Example full path:

`Enhancement > Causal-Conditional > Reason > hypotactic`

Example feature code:

`enh_caus_reason_hypo`

Example output columns:

- `intra_enh_caus_reason_hypo_raw`
- `intra_enh_caus_reason_hypo_per_1000`

The code generator should use a fixed mapping such as:

| Full label | Code |
|---|---|
| Extension | `ext` |
| Elaboration | `elab` |
| Enhancement | `enh` |
| Causal-Conditional | `caus` |
| Temporal | `temp` |
| Reason | `reason` |
| Result | `result` |
| Conditional | `cond` |
| Concessive | `conc` |
| paratactic | `para` |
| hypotactic | `hypo` |

Any label not present in the controlled mapping should be converted through a stable slugification rule and reviewed before release. The goal is stable, interpretable feature names, not shortest possible names.

## Design Principle: Do Not Overclaim

Grouped indices should aggregate only labels already assigned by the parser.

For example, if the parser assigns:

- `macro_category = Enhancement`
- `path_2 = Causal-Conditional`
- `path_3 = Reason`
- `taxis = hypotactic`

then a grouped index such as `enh_caus_reason_hypo` is justified because it reflects parser-assigned labels.

The output layer should not invent additional interpretive categories that were not assigned during parsing.

## Pros and Cons

### Pros

- Keeps text-level files compact and practical.
- Preserves full case-level evidence.
- Supports item-level analysis without producing extremely wide spreadsheets.
- Makes outputs easier to use in statistical workflows.
- Reduces risk from dictionary expansion.
- Keeps feature names stable through controlled abbreviation mapping.

### Cons

- Users who want one column per connector must pivot the long-format item file.
- Long-format item-level files require more statistical literacy than simple wide spreadsheets.
- A controlled abbreviation mapping must be maintained as the dictionary evolves.
- Documentation must clearly explain the relationship between case-level, text-level, and item-level outputs.

## Implementation Order

1. Implement the scalable output design first in `Conjunction_Research_V2`.
2. Test outputs on representative files and corpora.
3. Confirm that case-level evidence, compact text-level indices, and long-format item-level files align.
4. Port the stable logic to `/Users/joselema/conjuncTool_app`.
5. Update `INDEX_DESCRIPTIONS.md` and `USER_GUIDE.md`.
6. Rebuild the packaged app.

## Expected Outcome

The final output system should provide:

- detailed evidence for validation,
- compact text-level indices for analysis,
- long-format item-level statistics for connector-specific work,
- stable feature codes for grouped functional-path indices,
- and a design that remains usable as the dictionaries grow.

---

## Implementation Note: Intra-Sentential Supported Indices

The scalable output design has been implemented first for the intra-sentential supported index builder:

```text
scripts/build_v2_intrasentential_supported_indices.py
```

The builder now produces two main supported output files:

```text
outputs/v2_intrasentential_full/v2_intrasentential_full_supported_text_indices.csv
outputs/v2_intrasentential_full/v2_intrasentential_full_supported_item_indices.csv
```

The text-level file remains the main statistical file. It now includes compact grouped functional-path columns such as:

```text
intra_enh_caus_reason_hypo_raw
intra_enh_caus_reason_hypo_per_1000
intra_enh_caus_conc_para_raw
intra_enh_caus_conc_para_per_1000
intra_enh_temp_sim_para_raw
intra_enh_temp_sim_para_per_1000
```

The item-level file is long-format and preserves exact detected items without creating one wide column per conjunction. It includes:

```text
text_id
analysis_level
detected_item
feature_code
macro_category
path_2
path_3
path_4
path_5
taxis
raw_count
per_1000
word_count_text
word_count_source
```

Current successful run:

```text
supported_text_indices.csv: 238,697 rows; 117 columns; approximately 96 MB
supported_item_indices.csv: 377,924 rows; approximately 55 MB
```

This confirms that the scalable design works: exact items are preserved in a long-format item file, while the main text-level file remains compact enough for statistical analysis.

---

## Current Status and Next Validation Steps

Current completed work:

- ConjuncTool app produces scalable outputs:
  - `*_results.csv`
  - `*_text_indices.csv`
  - `*_item_indices.csv`
  - summary files
- The main statistical file is `*_text_indices.csv`.
- Exact conjunction items are preserved in `*_item_indices.csv` and `*_results.csv`.
- Output folder is `~/ConjuncTool_outputs/`.
- Packaged GUI app has been rebuilt and tested.
- Real corpus samples were created in `testing_corpus_samples/`.
- The V2 research project was used to validate a targeted filter for bare `rather`.
- The validated `rather` rule has been ported to the app parser.
- Bare intensifier/preference `rather` is excluded in supported intra-sentential mode.
- Valid replacive contexts remain supported:
  - `but rather`
  - `or rather`
  - `rather than`

Validation evidence:

- 4,000 sampled texts were tested in V2.
- 58,195 detected cases.
- 26,249 supported cases.
- 4 supported `rather` cases remained, all valid replacive contexts.
- Controlled app test returned 3 supported cases and excluded `rather low budget`.

Current checkpoint:

- `app_v2_rather_filter_ported_20260504_1554`

Next recommended validation work:

- Do not add major new GUI features yet.
- Continue parser validation one ambiguous item at a time.
- Candidate items:
  - `once`
  - `as`
  - `while`
  - `since`
  - `so`
  - `then`
  - `when`
  - `where`
  - `and`
  - `but`
  - `or`
  - `still`
- Recommended next candidate: `once`, because of possible false positives such as:
  - `Once upon a time`
  - `all at once`
  - `at once`

Recommended validation workflow:

1. Build targeted audit for one item.
2. Inspect examples.
3. Add rule only if evidence is strong.
4. Test on medium/random batch.
5. Port validated rule to app.
6. Document and checkpoint.

## Validation Update: `once` Filter

Date: 2026-05-04

A narrow ambiguity filter was added for `once` in the research pipeline parser.

Problem:

The parser was detecting `once` as a temporal hypotactic connector in cases where it functions as an adverb meaning `formerly` or `previously`, especially before adjectives.

Example false-positive pattern:

- the once strong bond
- the once famous actor
- the once-prestigious family
- the once beautiful countryside

Patch scope:

- File patched: `scripts/run_v2_intrasentential_full.py`
- Function patched: `is_risky_false_positive(...)`
- Rule added: exclude `once` only when followed by optional whitespace or hyphen plus a whitelisted adjective.
- No suffix-based adjective detection was used.
- No POS tagging was added.
- The dictionary was not changed.
- The validated `rather` rule was not changed.

Targeted validation:

- 15 audited `once + adjective` candidate spans were tested.
- 15/15 candidate false-positive spans were excluded by the patched parser.
- KEEP cases such as `once I arrived`, `once the system starts`, `once students finish`, `once this happens`, `once again`, and `once more` were retained.

Current status:

The `once` filter has passed targeted parser-level validation in the research pipeline. However, the full V2 corpus output file `outputs/v2_intrasentential_full/v2_intrasentential_full_cases.csv` has not yet been regenerated after the patch because the full EFCAMDAT rerun is time-consuming. Therefore, persisted full-output CSVs still reflect the pre-patch state until a full rerun is completed.

## Validation Update: `while` Noun-Phrase Filter

Date: 2026-05-04

A narrow false-positive filter was added for `while` noun-phrase uses where `while` means a period of time rather than a connector.

Examples excluded:

- after a while
- for a while
- once in a while
- in a while
- it's been a while
- takes a while
- learner punctuation variants such as `for a,while`

Patch scope:

- File patched: `scripts/run_v2_intrasentential_full.py`
- Function patched: `is_risky_false_positive(...)`
- No dictionary changes.
- No changes to `rather` or `once`.
- No broad temporal/contrastive reclassification of `while`.

Targeted validation:

- 109 audited noun-phrase candidate spans were tested.
- 109/109 were removed by the patched parser.
- Non-noun-phrase `while` cases such as `while I waited` and `while driving` were retained.

Current status:

The `while` noun-phrase filter has passed targeted parser-level validation in the research pipeline. Full corpus outputs have not yet been regenerated after this patch.


## Validation Update: `once in a while` Idiom Filter

Date: 2026-05-05

The existing `once` false-positive logic was extended to exclude the idiomatic frequency expression `once in a while` / `once in awhile`.

Patch scope:

- File patched: `scripts/run_v2_intrasentential_full.py`
- Function patched: `is_risky_false_positive(...)`
- No dictionary changes.
- No changes to `rather` or `while`.
- No app files changed.

Targeted validation:

- `We meet once in a while.` → once hits: 0
- `We meet once in awhile.` → once hits: 0
- `I called once I arrived.` → once hits: 1
- `He tried once again.` → once hits: 1

Current status:

The `once in a while` idiom filter has passed targeted parser-level validation in the research pipeline. Full corpus outputs have not yet been regenerated after this patch.


## Validation Update: `once in a while` Idiom Filter

Date: 2026-05-05

The existing `once` false-positive logic was extended to exclude the idiomatic frequency expression `once in a while` / `once in awhile`.

Patch scope:

- File patched: `scripts/run_v2_intrasentential_full.py`
- Function patched: `is_risky_false_positive(...)`
- No dictionary changes.
- No changes to `rather` or `while`.
- No app files changed.

Targeted validation:

- `We meet once in a while.` → once hits: 0
- `We meet once in awhile.` → once hits: 0
- `I called once I arrived.` → once hits: 1
- `He tried once again.` → once hits: 1

Current status:

The `once in a while` idiom filter has passed targeted parser-level validation in the research pipeline. Full corpus outputs have not yet been regenerated after this patch.


## Audit Update: `so`

Date: 2026-05-05

A validation-only audit was conducted for supported `so` cases to determine whether an additional false-positive filter was justified.

Diagnostic summary:

- All `so` detections: 47,947
- Unsupported by lexical priming: 30,227
- Supported by lexical priming: 17,720

The supported cases were audited using prescriptive grammar categories and span-local checks.

Final audit interpretation:

- Most supported `so` cases were result-clause candidates, such as `so I`, `so we`, `so they`, `so the`, and similar clause-like continuations.
- Apparent idiom cases were reviewed span-locally to avoid misclassifying valid result `so` cases in sentences that also contained later expressions such as `and so on`.
- Learner-English patterns such as `I think so you...` and `I hope so you...` were not treated as automatic exclusions, because they may function as non-standard complement/that-like constructions in learner writing.
- No high-confidence supported false-positive pattern remained after audit refinement.

Decision:

No parser patch was applied for `so`.

Current status:

`so` has been audited. Lexical priming already filters many ambiguous cases, and the supported survivors do not currently justify a narrow false-positive rule.


## Audit Update: `still`

Date: 2026-05-05

A priming diagnostic was run for `still` to determine whether a supported-survivor audit or false-positive patch was needed.

Diagnostic summary:

- All `still` detections: 5,548
- Supported by lexical priming: 0
- Unsupported by lexical priming: 5,548

Priming decisions:

- ambiguous: 5,420
- possibly_clause_like: 128

Decision:

No parser patch was applied for `still`.

Current status:

`still` does not currently enter the supported intra-sentential output. Lexical priming already blocks all detected `still` cases, so no additional false-positive filter is needed at this stage.


## Audit Update: `yet`

Date: 2026-05-05

A priming diagnostic was run for `yet` to determine whether a supported-survivor audit or false-positive patch was needed.

Diagnostic summary:

- All `yet` detections: 1,685
- Supported by lexical priming: 0
- Unsupported by lexical priming: 1,685

Priming decisions:

- ambiguous: 1,567
- possibly_clause_like: 118

Decision:

No parser patch was applied for `yet`.

Current status:

`yet` does not currently enter the supported intra-sentential output. Lexical priming already blocks all detected `yet` cases, so no additional false-positive filter is needed at this stage.


## Audit Update: `since`

Date: 2026-05-05

A validation-only audit was conducted for supported `since` cases.

Diagnostic summary:

- All `since` detections: 4,013
- Supported by lexical priming: 2,854
- Unsupported by lexical priming: 1,159

Supported priming decisions:

- possibly_clause_like: 1,663
- temporal_likely: 1,191

Audit categories:

- keep_since_causal_clause_candidate: 788
- keep_since_clause_candidate: 498
- review_since_temporal_adjunct: 962
- review_since_then_ever_since: 135
- review: 471

Interpretation:

The main issue for `since` is not a simple false-positive pattern. Many supported cases are temporal adjuncts such as `since 2004`, `since last year`, `since yesterday`, `since then`, and `ever since`. These are semantically temporal enhancement uses, but they do not always function as clause-linking conjunctions.

Decision:

No parser patch was applied for `since`.

Current status:

`since` has been audited. Temporal-adjunct uses should be interpreted cautiously in analysis and documentation rather than automatically filtered from the parser at this stage.


## Audit Update: `then`

Date: 2026-05-05

A validation-only audit was conducted for supported `then` cases.

Diagnostic summary:

- All `then` detections: 29,198
- Supported by lexical priming: 8,474
- Unsupported by lexical priming: 20,724

Supported priming decisions:

- possibly_clause_like: 8,474

Audit categories:

- keep_then_sequence_clause: 6,533
- keep_if_then_consequence: 1,264
- review: 594
- review_then_temporal_adjunct: 78
- review_then_idiom_frequency: 5

Interpretation:

Most supported `then` cases function as sequence or consequence markers. Review cases such as `since then`, `from then`, `by then`, and `until then` are temporal-adjunct/discourse-temporal uses rather than simple false positives. Very rare idiom-frequency cases such as `now and then` were observed but were not frequent enough to justify a parser patch at this stage.

Decision:

No parser patch was applied for `then`.

Current status:

`then` has been audited. The supported cases are mostly valid sequence/consequence uses, and remaining review cases should be interpreted cautiously rather than automatically filtered.


## Ambiguity Validation Summary

| Item / pattern | Main issue | Evidence / diagnostic result | Decision | Research parser | App parser | Packaged app test | Status |
|---|---|---|---|---|---|---|---|
| `rather` | Degree adverb vs connector | Standalone `rather` false positives; valid `rather than` retained | Patch narrow filter | Patched | Ported | Passed | Complete |
| `once + ADJ` | `once` = formerly/previously, not temporal connector | 15/15 audited `once + adjective` spans removed in targeted validation | Patch whitelist-based filter | Patched | Ported | Passed | Complete |
| `while` noun phrase | `while` = period of time, not connector | 109/109 noun-phrase candidates removed | Patch noun-phrase idiom filter | Patched | Ported | Passed | Complete |
| `once in a while` | Frequency idiom, not temporal connector | Targeted test: `once in a while` → 0 hits; clause uses retained | Extend `once` filter | Patched | Ported | Passed | Complete |
| `so` | Result connector vs intensifier/idiom/learner complement | 47,947 detections; 30,227 blocked by priming; 17,720 supported; no safe false-positive pattern after audit | No patch | No patch | Not needed | Not needed | Audited |
| `still` | Continuative adverb vs concessive marker | 5,548 detections; 0 supported by priming | No patch | No patch | Not needed | Not needed | Audited |
| `yet` | Temporal adverb vs contrastive connector | 1,685 detections; 0 supported by priming | No patch | No patch | Not needed | Not needed | Audited |
| `since` | Clause-linking vs temporal adjunct | 4,013 detections; 2,854 supported; many `since 2004`, `since then`, `ever since` cases | No patch; interpret cautiously | No patch | Not needed | Not needed | Audited |
| `then` | Sequence/consequence marker vs temporal adjunct/idiom | 29,198 detections; 8,474 supported; mostly sequence/consequence; rare `now and then` | No patch; interpret cautiously | No patch | Not needed | Not needed | Audited |

Summary:

The validation cycle produced four implemented ambiguity filters and five audit-only decisions where lexical priming or theoretical interpretation made additional filtering unnecessary.


## Audit Update: `as`

Date: 2026-05-05

A validation-only audit was conducted for supported `as` cases.

Diagnostic summary:

- All `as` detections: 20,525
- Supported by lexical priming: 5,328
- Unsupported by lexical priming: 15,197

Audit categories:

- keep_as_clause_candidate: 5,022
- review: 267
- review_as_multiword_overlap: 36
- review_as_comparison: 2
- review_as_prepositional_like: 1

Interpretation:

The supported `as` cases were mostly clause-like uses, such as `as I`, `as you`, `as it`, `as he`, and `as they`. The main remaining review issue involved multiword-overlap cases, especially learner uses of `such as + clause/phrase`. These cases are not simple false positives because `such as` may function as an exemplification marker in the inventory. A few comparison cases such as `as ... as` and one prepositional-like case were observed, but they were too rare to justify a parser patch.

Decision:

No parser patch was applied for `as`.

Current status:

`as` has been audited. Lexical priming filters most ambiguous cases, and the remaining supported survivors do not currently justify a narrow false-positive rule. Multiword-overlap cases such as `such as` should be monitored separately.


## Updated Ambiguity Validation Summary

| Item / pattern | Main issue | Evidence / diagnostic result | Decision | Research parser | App parser | Packaged app test | Status |
|---|---|---|---|---|---|---|---|
| `rather` | Degree adverb vs connector | Standalone `rather` false positives removed; valid `rather than` retained | Patch narrow filter | Patched | Ported | Passed | Complete |
| `once + ADJ` | `once` = formerly/previously, not temporal connector | 15/15 audited `once + adjective` spans removed | Patch whitelist-based filter | Patched | Ported | Passed | Complete |
| `while` noun phrase | `while` = period of time, not connector | 109/109 noun-phrase candidates removed | Patch noun-phrase idiom filter | Patched | Ported | Passed | Complete |
| `once in a while` | Frequency idiom, not temporal connector | Targeted test: `once in a while` → 0 hits; clause uses retained | Extend `once` filter | Patched | Ported | Passed | Complete |
| `so` | Result connector vs intensifier/idiom/learner complement | 47,947 detections; 30,227 blocked by priming; no safe supported false-positive pattern after audit | No patch | No patch | Not needed | Not needed | Audited |
| `still` | Continuative adverb vs concessive marker | 5,548 detections; 0 supported by priming | No patch | No patch | Not needed | Not needed | Audited |
| `yet` | Temporal adverb vs contrastive connector | 1,685 detections; 0 supported by priming | No patch | No patch | Not needed | Not needed | Audited |
| `since` | Clause-linking vs temporal adjunct | 4,013 detections; 2,854 supported; many `since 2004`, `since then`, `ever since` cases | No patch; interpret cautiously | No patch | Not needed | Not needed | Audited |
| `then` | Sequence/consequence marker vs temporal adjunct/idiom | 29,198 detections; 8,474 supported; mostly sequence/consequence; rare `now and then` | No patch; interpret cautiously | No patch | Not needed | Not needed | Audited |
| `as` | Clause subordinator vs role/comparison/multiword overlap | 20,525 detections; 15,197 blocked by priming; 5,328 supported; 5,022 clause-like | No patch; monitor multiword overlap | No patch | Not needed | Not needed | Audited |

Summary:

The ambiguity-validation cycle currently includes four implemented filters and six audit-only decisions. Implemented filters address clear false-positive patterns. Audit-only decisions were made where lexical priming already blocked the item, where supported cases were mostly valid, or where the issue required theoretical interpretation rather than a safe parser patch.


## Updated Ambiguity Validation Summary

| Item / pattern | Main issue | Evidence / diagnostic result | Decision | Research parser | App parser | Packaged app test | Status |
|---|---|---|---|---|---|---|---|
| `rather` | Degree adverb vs connector | Standalone `rather` false positives removed; valid `rather than` retained | Patch narrow filter | Patched | Ported | Passed | Complete |
| `once + ADJ` | `once` = formerly/previously, not temporal connector | 15/15 audited `once + adjective` spans removed | Patch whitelist-based filter | Patched | Ported | Passed | Complete |
| `while` noun phrase | `while` = period of time, not connector | 109/109 noun-phrase candidates removed | Patch noun-phrase idiom filter | Patched | Ported | Passed | Complete |
| `once in a while` | Frequency idiom, not temporal connector | Targeted test: `once in a while` → 0 hits; clause uses retained | Extend `once` filter | Patched | Ported | Passed | Complete |
| `so` | Result connector vs intensifier/idiom/learner complement | 47,947 detections; 30,227 blocked by priming; no safe supported false-positive pattern after audit | No patch | No patch | Not needed | Not needed | Audited |
| `still` | Continuative adverb vs concessive marker | 5,548 detections; 0 supported by priming | No patch | No patch | Not needed | Not needed | Audited |
| `yet` | Temporal adverb vs contrastive connector | 1,685 detections; 0 supported by priming | No patch | No patch | Not needed | Not needed | Audited |
| `since` | Clause-linking vs temporal adjunct | 4,013 detections; 2,854 supported; many `since 2004`, `since then`, `ever since` cases | No patch; interpret cautiously | No patch | Not needed | Not needed | Audited |
| `then` | Sequence/consequence marker vs temporal adjunct/idiom | 29,198 detections; 8,474 supported; mostly sequence/consequence; rare `now and then` | No patch; interpret cautiously | No patch | Not needed | Not needed | Audited |
| `as` | Clause subordinator vs role/comparison/multiword overlap | 20,525 detections; 15,197 blocked by priming; 5,328 supported; 5,022 clause-like | No patch; monitor multiword overlap | No patch | Not needed | Not needed | Audited |

Summary:

The ambiguity-validation cycle currently includes four implemented filters and six audit-only decisions. Implemented filters address clear false-positive patterns. Audit-only decisions were made where lexical priming already blocked the item, where supported cases were mostly valid, or where the issue required theoretical interpretation rather than a safe parser patch.


## Diagnostic Update: `for`

Date: 2026-05-05

A priming diagnostic was run for standalone `for`.

Diagnostic summary:

- All `for` detections: 0
- Supported by lexical priming: 0

Decision:

No audit or parser patch was needed.

Current status:

Standalone `for` does not currently appear in the V2 intra-sentential output. This avoids the high false-positive risk associated with prepositional `for` uses such as `for students`, `for two years`, `for example`, and `for this reason`.


## Diagnostic Update: `like`

Date: 2026-05-05

A priming diagnostic was run for standalone `like`.

Diagnostic summary:

- All `like` detections: 0
- Supported by lexical priming: 0

Decision:

No audit or parser patch was needed.

Current status:

Standalone `like` does not currently appear in the V2 intra-sentential output. This avoids the high false-positive risk associated with verb, comparison, and prepositional uses such as `I like music`, `looks like`, `sounds like`, and `like a teacher`.


## Diagnostic Update: `only`

Date: 2026-05-05

A priming diagnostic was run for standalone `only`.

Diagnostic summary:

- All `only` detections: 0
- Supported by lexical priming: 0

Decision:

No audit or parser patch was needed.

Current status:

Standalone `only` does not currently appear in the V2 intra-sentential output. This avoids the high false-positive risk associated with focus-adverb uses such as `only one`, `only students`, and `only because`. Multiword forms such as `only if` or `only when`, if present in the inventory, should be handled separately as multiword connectors rather than as standalone `only`.

