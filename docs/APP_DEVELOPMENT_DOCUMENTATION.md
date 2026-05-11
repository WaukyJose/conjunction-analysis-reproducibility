## 1. Purpose of the app

ConjuncTool is being developed as a research-informed GUI application for analysing conjunctions and discourse markers across three discourse levels:

1. Intra-sentential conjunctions
2. Inter-sentential discourse markers
3. Inter-paragraph discourse markers

The app is intended to make the V2 conjunction-analysis pipeline usable beyond scripts, allowing users to input text, select an analysis mode, inspect detected markers, and export results.

---

## 2. Methodological basis

The app is based on a position-sensitive approach to conjunction analysis.

The main distinction is:

Structural / intra-sentential use
= conjunctions inside sentence boundaries, approximating clause-linking environments

Cohesive / discourse-level use
= markers at sentence or paragraph boundaries linking discourse units

The app must keep the three analysis levels separate:

within sentence
between sentences
between paragraphs

---

## 3. Validation-informed design principle

Manual validation showed that not all detection layers are equally reliable.

Therefore, the app should distinguish between:

Broad / exploratory indices
Validated / supported indices

Main rule:

Supported or validated indices should be used for interpretation.
Broad indices should be treated as exploratory/descriptive.

This is especially important for intra-sentential analysis, where broad detection can include phrase-level coordination and token-boundary false positives.

---

## 4. Planned app analysis modes

The GUI should eventually provide four clear options:

1. Intra-sentential — Broad / exploratory
2. Intra-sentential — Supported / validated
3. Inter-sentential — Validated
4. Inter-paragraph — Validated

Recommended user-facing descriptions:

Intra-sentential — Broad / exploratory:
Detects broad within-sentence connector use. Useful for descriptive exploration, but not recommended as the main inferential layer.

Intra-sentential — Supported / validated:
Recommended for interpretation. Applies additional filtering to improve clause-linking validity.

Inter-sentential — Validated:
Detects sentence-initial discourse markers linking a sentence to previous discourse.

Inter-paragraph — Validated:
Detects paragraph-initial discourse markers linking a paragraph to previous paragraph-level discourse. Requires preserved paragraph breaks.

---

## 5. Validation evidence

### 5.1 Intra-sentential validation

Manual validation showed that intra-sentential detection is the most difficult layer.

Key findings:

Random sample:
n = 300
valid detections = 69.0%

Risky / oversampled cases:
n = 150
valid detections = 62.7%

Supported / primed cases:
substantially more reliable than unsupported broad cases

Main false-positive sources:

- and/or linking noun phrases, adjectives, names, or list items
- so used as an intensifier, e.g. “so cute”, “so much”, “so sorry”
- as in expressions such as “such as”, “as well”, “working as”, “considered as”
- then in number sequences, sentence-final adverbials, or “by then”
- while in noun phrases such as “a while”
- because of and after + noun phrase where no finite clause follows
- token-boundary errors, e.g. and in “standing” or “husband”, or in “story/director/for”

Interpretation:

The intra-sentential broad layer is useful for exploratory evidence of within-sentence connector presence.
The supported intra-sentential layer should be used for clause-linking-oriented interpretation.

---

### 5.2 Inter-sentential validation

Manual validation of random inter-sentential cases showed strong performance.

Key findings:

Random sample:
n = 150

valid inter-sentential detections = 100%
discourse-linking valid = 100%
macro category correct or acceptable = 100%

supported subset = 148/150
unsupported/broad subset = 2/150

Interpretation:

The inter-sentential parser is stable because detection is restricted to sentence-initial discourse-marker sequences.

This positional restriction reduces common intra-sentential false positives such as phrase-level coordination and token-boundary errors.

---

### 5.3 Inter-paragraph validation

Manual validation of random inter-paragraph cases also showed strong performance.

Key findings:

Random sample:
n = 100

COREFL = 50
GiG = 50
EFCAMDAT excluded because paragraph boundaries are not preserved

valid inter-paragraph detections = 100%
paragraph-linking valid = 100%
macro category correct or acceptable = 100%

supported subset = 100/100
unsupported/broad subset = 0/100

Interpretation:

The inter-paragraph parser is the most constrained layer because detection is restricted to paragraph-initial markers in texts with preserved paragraph boundaries.

Important caveat:

Validation confirms high precision for detected markers.
Recall was not estimated because undetected cohesive links were not manually searched.

---

## 6. App architecture principle

The app should follow a modular structure.

Recommended architecture:

conjuncTool_app/
│
├── run_app.py
├── README.md
├── APP_DEVELOPMENT_DOCUMENTATION.md
├── requirements.txt
│
├── app/
│ ├── gui.py
│ ├── analysis_engine.py
│ ├── export_utils.py
│ └── config.py
│
├── resources/
├── samples/
└── outputs/

Design rule:

gui.py should handle only the interface and user interaction.
analysis_engine.py should connect the GUI to the parser logic.
export_utils.py should handle saving/exporting outputs.
config.py should handle paths and reusable settings.

This avoids mixing GUI code, analysis logic, and export logic in the same file.

---

## 7. Minimum viable app

The first stable app version should support:

Paste text
Select analysis mode
Run analysis
View detected markers in a table
Export results

The first stable version should not yet focus on:

large batch processing
folder-level corpus processing
advanced visualisations
statistical testing

Those should be added only after the single-text analysis workflow is stable.

---

## 8. Minimum output fields

The app should aim to display/export fields such as:

detected_item
analysis_level
sentence_or_paragraph_context
macro_category
subtype_or_path
position
confidence
supported_flag
notes

For inter-sentential and inter-paragraph analysis, the app should also preserve enough context to show how the marker links discourse units.

---

## 9. User guidance inside the app

The app should include short help text explaining the methodological status of each mode.

Suggested help text:

Broad intra-sentential mode is exploratory and may include phrase-level coordination.

Supported intra-sentential mode is recommended for clause-linking interpretation.

Inter-sentential mode detects validated sentence-initial discourse markers.

Inter-paragraph mode detects validated paragraph-initial discourse markers and requires preserved paragraph breaks.

---

## 10. Immediate development step

Before editing the app, inspect the current files:

sed -n '1,260p' run_app.py
echo "----- app/gui.py -----"
sed -n '1,360p' app/gui.py
echo "----- app/export_utils.py -----"
sed -n '1,260p' app/export_utils.py
echo "----- requirements.txt -----"
cat requirements.txt

Then prepare a current architecture map and identify the smallest safe first code update.

---

## Development Milestone: Four-Mode App with Text-Level Indices

Current milestone achieved:

- The app runs as a Tkinter GUI.
- The app can also be run from the command line through `run_app.py`.
- Four analysis modes are available: `intra`, `intra_supported`, `intersent`, and `interpara`.
- The packaged macOS app runs successfully through PyInstaller.
- Outputs are saved to `~/ConjuncTool_outputs/`.
- Each analysis produces a case-level results CSV, summary CSVs, and a text-level `_text_indices.csv` file.
- Taxis summaries are produced where relevant.
- Per-1,000-word rates now use the full input text word count.

Current smoke-test outcomes:

- `sample_intra_text.txt` + `intra_supported` → 2 cases.
- `sample_text.txt` + `intersent` → 3 cases.
- `sample_paragraph_text.txt` + `interpara` → 2 cases.

Current app status: working V2 prototype suitable for further testing with user-supplied `.txt` files.

---

## V2 Research Pipeline vs ConjuncTool App Status

- `Conjunction_Research_V2` is the research/validation pipeline.
- `conjuncTool_app` is the user-facing Tkinter/downloadable app.
- Scalable outputs are already implemented in the app:
  - `_results.csv`
  - `_text_indices.csv`
  - `_item_indices.csv`
- The `rather` filter has been validated in the V2 research pipeline.
- Current app status: the validated `rather` filter has been ported to the app parser and tested.
- Next app step: continue validation of other ambiguous items one at a time, beginning with `once`.

---

## Validation Update: `rather` Filter Ported to App

The validated V2 `rather` filter has now been ported to:

```text
app/parsers/intra_supported_v2.py
```

Controlled app-level test:

```text
The film had a rather low budget.
It did not fail but rather improved.
I would choose this rather than that.
This is, or rather was, the main point.
```

Expected supported output:

```text
Excluded:
- bare intensifier use: rather low budget

Kept:
- but rather
- rather than
- or rather
```

CLI app test result:

```text
Detected supported cases: 3
```

This confirms that bare `rather` is excluded from the supported intra-sentential output, while validated replacive contexts remain supported.

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

## Packaged App Test: `rather` Filter

Date: 2026-05-04

After porting the validated `rather` ambiguity filter into the app parser, the packaged GUI app was reopened and tested using real corpus sample files.

Evidence from `~/ConjuncTool_outputs/`:

- Fresh intra-supported output files were generated successfully.
- No standalone `rather` item was detected as an intra-sentential connector.
- One valid `rather than` case was retained.
- The phrase `rather low budget` appeared only inside the context sentence and was not extracted as a connector.

Result:

`rather` filter successfully passed the packaged-app validation test.

Current status:

The research-pipeline rule for `rather` has been validated, ported to the user-facing app, tested in the packaged app, and confirmed to behave correctly.

## App Parser Update: `once` Filter Ported

Date: 2026-05-04

The validated narrow `once` ambiguity filter from the research pipeline was ported to the user-facing app parser.

File patched:

- `app/parsers/intra_supported_v2.py`

Rule added:

Exclude `once` only when it is followed by optional whitespace or a hyphen plus a whitelisted adjective, where `once` means `formerly` or `previously` rather than functioning as a temporal connector.

Examples excluded:

- the once strong bond
- the once-prestigious family
- was once famous
- the once beautiful countryside

Examples retained:

- once I arrived
- once the system starts
- once students finish
- once this happens
- once again
- once more

Validation:

Targeted parser-level tests passed:

- `The once strong bond was gone.` → once hits: 0
- `The once-prestigious family declined.` → once hits: 0
- `He tried once again.` → once hits: 1
- `I called my friend once I arrived.` → once hits: 1
- `The output is generated once the system starts.` → once hits: 1

No GUI files, dictionary files, export logic, or `rather` rules were changed.

Current status:

The `once` filter has been ported to the app parser and passed targeted parser-level validation. The packaged app has not yet been rebuilt or tested after this change.


## Packaged App Test: `once` Filter

Date: 2026-05-04

After porting the validated narrow `once` ambiguity filter into the app parser, the packaged ConjuncTool app was rebuilt and tested through the GUI.

Test mode:

- Intra-sentential supported analysis

Evidence from fresh output folder:

- Fresh supported output files were generated at May 4 17:00–17:03.
- Output files used the expected supported pattern: `*_intra_supported_results.csv`.
- The previous false-positive context `once strong and inseparable bond` appeared only inside the sentence context for another connector (`so that`).
- No row detected standalone `once` as a connector in that false-positive context.

Result:

The `once` filter successfully passed the packaged-app validation test.

Current status:

The `once` ambiguity filter has been validated in the research parser, ported to the app parser, rebuilt into the packaged GUI app, and confirmed through fresh GUI output.


## App Parser Update: `while` Noun-Phrase Filter Ported

Date: 2026-05-05

The validated `while` noun-phrase false-positive filter was ported to the app parser.

File patched:

- `app/parsers/intra_supported_v2.py`

Rule added:

Exclude `while` only when it occurs in noun-phrase period-of-time expressions such as:

- after a while
- for a while
- once in a while
- it's been a while
- takes a while

Validation:

Targeted parser-level tests passed:

- `I waited for a while.` → while hits: 0
- `After a while he returned.` → while hits: 0
- `We meet once in a while.` → while hits: 0
- `I read while I waited.` → while hits: 1
- `I had breakfast while driving.` → while hits: 1
- `The output changes while the system starts.` → while hits: 1

No GUI, dictionary, export, spec, `rather`, or `once` files were changed.

Current status:

The `while` noun-phrase filter has been ported to the app parser and passed targeted parser-level validation. The packaged app has not yet been rebuilt or tested after this change.


## App Parser Update: `while` Noun-Phrase Filter Ported

Date: 2026-05-05

The validated `while` noun-phrase false-positive filter was ported to the app parser.

File patched:

- `app/parsers/intra_supported_v2.py`

Rule added:

Exclude `while` only when it occurs in noun-phrase period-of-time expressions such as:

- after a while
- for a while
- once in a while
- it's been a while
- takes a while

Validation:

Targeted parser-level tests passed:

- `I waited for a while.` → while hits: 0
- `After a while he returned.` → while hits: 0
- `We meet once in a while.` → while hits: 0
- `I read while I waited.` → while hits: 1
- `I had breakfast while driving.` → while hits: 1
- `The output changes while the system starts.` → while hits: 1

No GUI, dictionary, export, spec, `rather`, or `once` files were changed.

Current status:

The `while` noun-phrase filter has been ported to the app parser and passed targeted parser-level validation. The packaged app has not yet been rebuilt or tested after this change.


## Packaged App Test: `while` Noun-Phrase Filter

Date: 2026-05-05

After porting the validated `while` noun-phrase filter into the app parser, the packaged ConjuncTool app was rebuilt and tested through the GUI.

Test mode:

- Intra-sentential supported analysis

Manual test file:

- `I waited for a while.`
- `After a while he returned.`
- `We meet once in a while.`
- `I read while I waited.`
- `I had breakfast while driving.`

Result:

- `for a while` was not detected as `while`.
- `after a while` was not detected as `while`.
- `once in a while` was not detected as `while`.
- `while I waited` was retained.
- `while driving` was retained.

The packaged-app `while` noun-phrase filter passed validation.

Additional observation:

The sentence `We meet once in a while.` still detected `once`. This is a separate `once` idiom issue and should be handled in a later `once` filter update, not as part of the `while` patch.


## Packaged App Test: `while` Noun-Phrase Filter

Date: 2026-05-05

After porting the validated `while` noun-phrase filter into the app parser, the packaged ConjuncTool app was rebuilt and tested through the GUI.

Test mode:

- Intra-sentential supported analysis

Manual test file:

- `I waited for a while.`
- `After a while he returned.`
- `We meet once in a while.`
- `I read while I waited.`
- `I had breakfast while driving.`

Result:

- `for a while` was not detected as `while`.
- `after a while` was not detected as `while`.
- `once in a while` was not detected as `while`.
- `while I waited` was retained.
- `while driving` was retained.

The packaged-app `while` noun-phrase filter passed validation.

Additional observation:

The sentence `We meet once in a while.` still detected `once`. This is a separate `once` idiom issue and should be handled in a later `once` filter update, not as part of the `while` patch.


## App Parser Update: `once in a while` Idiom Filter

Date: 2026-05-05

The existing app-side `once` false-positive logic was extended to exclude the idiomatic frequency expression `once in a while` / `once in awhile`.

File patched:

- `app/parsers/intra_supported_v2.py`

Targeted validation:

- `We meet once in a while.` → once hits: 0
- `We meet once in awhile.` → once hits: 0
- `I called once I arrived.` → once hits: 1
- `He tried once again.` → once hits: 1

No `rather`, `while`, dictionary, GUI, export, or spec files were changed.

Current status:

The app parser has passed targeted validation. The packaged app has not yet been rebuilt or tested after this patch.


## Packaged App Test: `once in a while` Idiom Filter

Date: 2026-05-05

After extending the app-side `once` filter, the packaged ConjuncTool app was tested through the GUI in intra-sentential supported mode.

Manual test file included:

- `We meet once in a while.`
- `I read while I waited.`
- `I had breakfast while driving.`

Result:

- `once in a while` was not detected as `once`.
- `while I waited` was retained.
- `while driving` was retained.

The packaged-app `once in a while` idiom filter passed validation.


## App Alignment Update After Extended Ambiguity Audit

Date: 2026-05-05

The research pipeline completed an extended ambiguity-validation pass after the app-side filters for `rather`, `once`, and `while` had already been ported and tested.

Implemented filters already present in the app:

- `rather` degree-adverb filter, while retaining `rather than`
- `once + adjective` formerly/previously filter
- `while` noun-phrase filter, e.g. `for a while`, `after a while`
- `once in a while` idiom filter

Additional research-side audit-only items:

- `so`
- `still`
- `yet`
- `since`
- `then`
- `as`
- `for`
- `like`
- `only`

Decision:

No app parser changes are needed for these audit-only items at this stage.

Reason:

- `so`, `since`, `then`, and `as` were audited but did not justify safe parser patches.
- `still` and `yet` had zero supported survivors after lexical priming.
- standalone `for`, `like`, and `only` had zero detections in the V2 intra-sentential output.
- Therefore, the app parser remains aligned with the current implemented research-pipeline filters.

Current app status:

The app parser is aligned with all implemented ambiguity filters. No GUI, export, dictionary, or packaging changes are required for the audit-only items.


## App Alignment Update After Extended Ambiguity Audit

Date: 2026-05-05

The research pipeline completed an extended ambiguity-validation pass after the app-side filters for `rather`, `once`, and `while` had already been ported and tested.

Implemented filters already present in the app:

- `rather` degree-adverb filter, while retaining `rather than`
- `once + adjective` formerly/previously filter
- `while` noun-phrase filter, e.g. `for a while`, `after a while`
- `once in a while` idiom filter

Additional research-side audit-only items:

- `so`
- `still`
- `yet`
- `since`
- `then`
- `as`
- `for`
- `like`
- `only`

Decision:

No app parser changes are needed for these audit-only items at this stage.

Reason:

- `so`, `since`, `then`, and `as` were audited but did not justify safe parser patches.
- `still` and `yet` had zero supported survivors after lexical priming.
- standalone `for`, `like`, and `only` had zero detections in the V2 intra-sentential output.
- Therefore, the app parser remains aligned with the current implemented research-pipeline filters.

Current app status:

The app parser is aligned with all implemented ambiguity filters. No GUI, export, dictionary, or packaging changes are required for the audit-only items.


## Final Smoke Test: V2 Ambiguity-Filter Milestone

Date: 2026-05-05

A final packaged-app smoke test was run after aligning the app with the implemented ambiguity filters.

Test mode:

- Intra-sentential supported analysis

Manual test folder:

- `~/conjuncTool_app/while_manual_test`

Output folder:

- `~/ConjuncTool_outputs_final_smoke_test`

Evidence:

- Fresh output files were generated at May 5 15:50.
- `once in a while` produced no detected `once` row.
- `while I waited` was retained.
- `while driving` was retained.

Result:

The packaged ConjuncTool app passed the final smoke test for the current V2 ambiguity-filter milestone.

Current stable milestone:

Implemented and app-tested filters:

- `rather`
- `once + adjective`
- `while` noun phrase
- `once in a while`

Research-audited items requiring no app patch:

- `so`
- `still`
- `yet`
- `since`
- `then`
- `as`
- `for`
- `like`
- `only`

Status:

ConjuncTool V2 ambiguity-filter milestone is stable.


## Final Smoke Test: V2 Ambiguity-Filter Milestone

Date: 2026-05-05

A final packaged-app smoke test was run after aligning the app with the implemented ambiguity filters.

Test mode:

- Intra-sentential supported analysis

Manual test folder:

- `~/conjuncTool_app/while_manual_test`

Output folder:

- `~/ConjuncTool_outputs_final_smoke_test`

Evidence:

- Fresh output files were generated at May 5 15:50.
- `once in a while` produced no detected `once` row.
- `while I waited` was retained.
- `while driving` was retained.

Result:

The packaged ConjuncTool app passed the final smoke test for the current V2 ambiguity-filter milestone.

Current stable milestone:

Implemented and app-tested filters:

- `rather`
- `once + adjective`
- `while` noun phrase
- `once in a while`

Research-audited items requiring no app patch:

- `so`
- `still`
- `yet`
- `since`
- `then`
- `as`
- `for`
- `like`
- `only`

Status:

ConjuncTool V2 ambiguity-filter milestone is stable.

