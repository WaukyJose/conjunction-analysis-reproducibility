# Parser V2 design

## Aim

Parser V2 aims to build a cleaner, manuscript-aligned version of the conjunction parser using the same filtered datasets but stricter Halliday index definitions and conservative position/context rules.

## Core principle

V2 should change the parser logic, not the data source.

Formula:

`same filtered data + stricter parser = controlled sensitivity test`

## Input datasets

Parser V2 uses:

- `data_filtered/efcamdat_v2_filtered.csv`
- `data_filtered/ielts_v2_filtered.csv`
- `data_filtered/gig_v2_filtered.csv`

## Grouping variables

- EFCAMDAT: `cefr`
- IELTS: `band`
- GiG: `year_group`

## Dictionary/index structure

Main index counts must match manuscript Table 3:

| Level | Elaboration | Extension | Enhancement | Total |
|---|---:|---:|---:|---:|
| Intra-sentential | 6 | 8 | 19 | 33 |
| Inter-sentential | 9 | 6 | 23 | 38 |
| Inter-paragraph | 9 | 6 | 23 | 38 |

## Dictionary files

- Intra-sentential: `resources/halliday_intrasent_dic.py`
- Inter-sentential: `resources/halliday_intersent_dic.py`
- Inter-paragraph: `resources/halliday_paragraph_dict.py`

## Paragraph dictionary decision

The paragraph dictionary contains an additional Extension category:

`Stance_Markers`

This category is excluded from the main V2 paragraph-level analysis because it is not part of the manuscript Table 3 index structure.

It may be retained only as an optional exploratory diagnostic feature.

## Intra-sentential V2 rules

V2 should reduce obvious false positives by filtering:

- lexical `like`
- existential `there`
- anaphoric/formulaic `this is`
- complement or relative `that` where possible
- `and/or` used only for noun/list coordination rather than clause-level linkage

## Inter-sentential V2 rules

V2 should detect only the first discourse-marker sequence at the beginning of the current sentence.

It should not classify a later dictionary item inside the sentence as the inter-sentential connector.

## Inter-paragraph V2 rules

V2 should make true paragraph-level claims only for texts with explicit newline paragraph boundaries.

Given the current cleaned datasets:

- GiG supports true paragraph-level analysis in most texts.
- EFCAMDAT and IELTS do not preserve paragraph boundaries in the cleaned files.

Therefore, main V2 inter-paragraph analysis should be restricted to GiG unless raw paragraph boundaries are recovered later.

## Sensitivity strategy

V2 should first be tested on a sample before full rerun.

Suggested first sample:

- EFCAMDAT: 1,000 texts
- IELTS: 1,000 essays
- GiG: 1,000 texts, or all GiG if computationally manageable

Compare V1 vs V2 using:

- total counts
- normalized counts
- macro-category proportions
- group rankings
- correlation between V1 and V2 indices

## Decision rule

If V2 improves construct validity and preserves broad corpus/group patterns, proceed to full V2 rerun.

If V2 substantially changes rankings or major findings, revise the results narrative around the refined indices.

## Inter-sentential pilot refinement

A pilot validation sample showed that broad sentence-initial items created false positives. V2 therefore excludes the following exact bare markers from the main inter-sentential analysis:

- `there`
- `as`
- `for`
- `with`
- `that`
- `this is`
- `here`

Additional contextual exclusions:

- exclude `in case` when followed by `study/studies`
- exclude fragment-only `so`

These changes reduced sample detections from 8,487 to 8,441 after the first broad-risk filter, removing only obvious noise and preserving the main distributional pattern.

## Intra-sentential pilot refinement log

Initial intra-sentential V2 sampling showed that several high-frequency dictionary items produced likely false positives because they often functioned as complementisers, prepositions, lexical verbs, or focus expressions rather than reliable intra-sentential Halliday expansion markers.

Items identified for exclusion from the main intra-sentential V2 analysis:

- `that`
- `by`
- `like`
- `through`
- `using`
- `especially`
- `the way`

Additional contextual rule:

- bare `as` is excluded when it occurs inside larger formulaic/comparative expressions such as:
  - `as well as`
  - `as soon as`
  - `as ... as`

These refinements are based on pilot inspection of V2 sample detections and are intended to improve construct validity while preserving the main taxis distinction: `paratactic` vs `hypotactic`.

## Intra-sentential taxis extraction

The intra-sentential dictionary stores taxis labels at different path depths depending on the index structure.

Observed structure:

- some indices store `paratactic` / `hypotactic` in `path_3`
- most indices store `paratactic` / `hypotactic` in `path_4`

Therefore, V2 does not assume a fixed path column. Instead, it extracts taxis dynamically:

`taxis = first value in path_2, path_3, path_4, or path_5 that equals paratactic or hypotactic`

This ensures that all intra-sentential macro categories, including Elaboration, are included in taxis-level summaries.

V2 exports separate intra-sentential summaries for:

- total detected cases
- macro-category counts
- taxis counts
- taxis × macro-category counts

## Intra-sentential pilot validation findings

A small V2 intra-sentential validation sample showed that the parser now captures the taxis distinction correctly, but still over-detects some phrase-level or formulaic patterns as clause-level intra-sentential conjunctions.

Main false-positive families identified:

- `and` / `or` inside noun phrases rather than clause-level coordination  
  - examples: `hair and brown eyes`, `films and television`, `McDonalds or KFC`
- `and` in fixed expressions  
  - example: `more and more`
- `and` linking low-level adjective or verb phrases, where the case is weak as clause-level taxis  
  - examples: `exciting and great fun`, `talk on the phone and send emails`
- `as` functioning as a preposition or role/comparison marker rather than temporal hypotaxis  
  - examples: `end up as`, `come across as`, `looked at us as`
- `that is` in relative constructions rather than elaborating/appositive conjunction  
  - example: `pin that is knocked down`
- `then` inside fixed temporal adverbials rather than as a paratactic connector  
  - example: `just then`
- cases caused by sentence-boundary noise, where a sentence-initial item after a period is incorrectly treated as intra-sentential.

Interpretive consequence:

The current intra-sentential V2 parser is suitable for detecting broad conjunction candidates, but further filtering is needed before full analysis if the goal is to approximate clause-level taxis rather than all local coordination.

Next refinement target:

`same intra dictionary + stronger phrase-level filters = cleaner clause-level approximation`

## Intra-sentential fixed-expression refinement

During intra-sentential pilot inspection, `and` was sometimes detected inside fixed expressions rather than as a clause-level paratactic connector.

Implemented fixed-expression exclusions:

- `more and more`
- `in and out`

The `in and out` rule targets only the connector inside the fixed phrase (`in [and] out`). Other `and` tokens in the same sentence are still retained if detected separately.

## Check against previous intra-sentential validation

The previous intra-sentential validation sample showed four major error families:

1. lexical false positives (`like`, `that`, `by`, `through`, `especially`, `here`);
2. sentence-initial discourse markers incorrectly counted as intra-sentential;
3. broad phrase-level coordination with `and` / `or`;
4. category/taxis ambiguity for items such as `also`, `moreover`, `however`, `therefore`, `then`, and `as`.

V2 has addressed the first two families and partly addressed `as` and fixed expressions such as `more and more` and `in and out`.

The remaining major unresolved issue is broad `and/or` phrase-level coordination. This will require conservative phrase-level filters before full V2 intra-sentential analysis.

## Intra-sentential prompt-formula refinement

The intra-sentential pilot showed that IELTS prompt formulae such as `agree or disagree` were being detected as intra-sentential alternation.

Implemented exclusion:

- `agree or disagree`

This removes prompt/task wording rather than learner-produced clause-level conjunction use.

## Intra-sentential additive/intensifier refinement

Further pilot validation showed that some frequent sentence-internal items were functioning as intensifiers, additive adverbs, frequency expressions, or named-entity artefacts rather than clause-level conjunctions.

Implemented exclusions:

- `too` as intensifier
- sentence-internal `also`
- `once` in frequency expressions such as `once a day/week/month/year`
- `so` in the place-name artefact `So Paulo`

These exclusions reduced clear non-conjunctive detections while preserving core paratactic and hypotactic markers such as `and`, `but`, `because`, `if`, `when`, and `before`.

## Intra-sentential contextual-filter verification

After applying contextual filters, follow-up inspection showed that remaining sentences containing `more and more` or `agree or disagree` did not retain the filtered connector inside those fixed expressions. Remaining detections were separate `and` / `or` tokens elsewhere in the same sentences.

Therefore, the contextual filters are functioning as intended:

- `more [and] more` is excluded;
- `agree [or] disagree` is excluded;
- other independently detected `and` / `or` tokens in the same sentence are retained.

The remaining `and` / `or` detections should be interpreted as broad coordination candidates, not guaranteed full clause-complex boundaries.

## Inter-paragraph V2 pilot refinement

V2 inter-paragraph analysis is restricted to GiG texts with explicit newline paragraph boundaries. EFCAMDAT and IELTS are excluded from main true paragraph-level analysis unless raw paragraph boundaries are recovered later.

A 200-text GiG pilot sample detected 145 paragraph-initial cases before heading/prompt filtering.

The following paragraph-initial items were excluded because pilot inspection showed they were mostly headings, prompts, or task-instruction artefacts rather than paragraph-level conjunctions:

- `should`
- `consider`
- `results`

After this filter, the 200-text GiG pilot detected 137 cases:

- Elaboration = 19
- Extension = 53
- Enhancement = 65

These cases represent conservative paragraph-initial conjunction candidates based on explicit newline boundaries.

## Inter-paragraph validation checkpoint

A 30-case GiG-only inter-paragraph validation sample was reviewed after restricting the analysis to texts with explicit newline paragraph boundaries and excluding heading/prompt artefacts.

Approximate validation outcome:

- detection accuracy: 28/30
- position accuracy: 30/30
- main remaining errors:
  - line-break list fragments
  - quoted dialogue openings

This supports the V2 decision to treat inter-paragraph analysis as a GiG-only true paragraph-boundary analysis, rather than using pseudo-paragraph fallback segmentation for EFCAMDAT or IELTS.

## ConjuncTool V2 prototype milestone

After sample-stage validation of the V2 parsers, the current parser logic was transferred into a separate ConjuncTool application prototype.

The app is located outside the research pipeline folder:

`~/ConjuncTool_App`

The app currently includes:

- `intra_v2.py`
- `intersent_v2.py`
- `interpara_v2.py`
- `run_app.py`
- `gui.py`

The purpose of the app at this stage is not public release, but controlled parser execution:

`select text → choose level → run V2 parser → export CSV → inspect/validate results`

This supports TAACO-like development while keeping parser validation and methodological documentation in the research pipeline.

## ConjuncTool V2 prototype milestone

After sample-stage validation of the V2 parsers, the current parser logic was transferred into a separate ConjuncTool application prototype.

The app is located outside the research pipeline folder:

`~/ConjuncTool_App`

The app currently includes:

- `app/parsers/intra_v2.py`
- `app/parsers/intersent_v2.py`
- `app/parsers/interpara_v2.py`
- `run_app.py`
- `app/gui.py`

The purpose of the app at this stage is not public release, but controlled parser execution:

`select text → choose level → run V2 parser → export CSV → inspect/validate results`

This supports TAACO-like development while keeping parser validation and methodological documentation in the research pipeline.

## Inter-sentential macro-specific normalized indices

After the full inter-sentential V2 run, text-level macro-specific indices were generated from the case-level output.

Output file:

- `outputs/v2_intersentential_full/v2_intersentential_full_macro_text_indices.csv`

The file contains raw and normalized per-1,000-word indices for:

- inter-sentential elaboration
- inter-sentential extension
- inter-sentential enhancement

Mean normalized values per 1,000 words:

- COREFL: Elaboration = 0.32, Extension = 2.66, Enhancement = 6.97
- EFCAMDAT: Elaboration = 0.58, Extension = 1.65, Enhancement = 5.01
- GiG: Elaboration = 0.42, Extension = 2.42, Enhancement = 4.07

Across corpora, Enhancement is the dominant inter-sentential macro category. COREFL shows the highest Enhancement density, probably reflecting narrative/retelling task effects. Median values show many zero-detection texts, especially in EFCAMDAT and GiG, so inferential analysis should treat the distributions as highly skewed/zero-inflated.

## Intra-sentential dictionary taxis audit

After the intra-sentential dictionary update, the regenerated V2 dictionary inventory was audited for taxis coverage.

Audit result:

- Total included intra-sentential rows: 198
- Paratactic rows: 120
- Hypotactic rows: 78
- Rows without taxis label: 0

By macro category:

| Macro category | Hypotactic | Paratactic |
|---|---:|---:|
| Elaboration | 8 | 34 |
| Enhancement | 55 | 60 |
| Extension | 15 | 26 |

This confirms that the updated intra-sentential dictionary explicitly assigns a taxis value to every included connector entry.

Interpretive note:

The dictionary layer is structurally complete with respect to taxis. Remaining uncertainty is not caused by missing taxis labels, but by contextual ambiguity in use. For example, a connector such as `and` may be dictionary-coded as paratactic, but in context it may link noun phrases, verb phrases, or full clauses. Therefore, intra-sentential taxis labels should be interpreted as dictionary-defined candidate values, not guaranteed syntactic clause-complex parses in every case.

## Parser-level treatment of multifunctional intra-sentential forms

The updated intra-sentential dictionary contains duplicate surface forms where the same lexical item may realise more than one Hallidayan function.

Examples include:

- `as`
- `since`
- `while`
- `when`
- `then`
- `so`
- `but`
- `however`
- `whereas`
- `yet`
- `and`
- `or`

These duplicates are retained in the dictionary because they represent theoretically plausible multifunctionality, not dictionary errors.

### Design decision

The dictionary is treated as the theoretical inventory:

`dictionary = possible Halliday categories and taxis values`

The parser is treated as the operational layer:

`parser = candidate detection + filtering + contextual/priming annotation`

Therefore, multifunctional forms will not be removed from the dictionary simply to force one category. Instead, the intra-sentential parser will mark selected forms as problematic/multifunctional and add lexical-priming/contextual annotation columns.

Planned parser-level annotation columns:

- `is_problematic_multifunctional`
- `priming_decision`
- `priming_confidence`
- `priming_notes`

### Interpretation

This separates two issues:

1. dictionary-level theoretical classification;
2. context-level syntactic or discourse-function ambiguity.

For example, `while` may be temporal, concessive, or adversative depending on context. Similarly, `and` may link noun phrases, verb phrases, or full clauses. These contextual differences cannot be fully resolved by dictionary membership alone.

The planned lexical-priming layer will therefore be used only for problematic multifunctional forms, not for all connectors. Clear markers such as `because`, `although`, `even though`, `so that`, `rather than`, and `instead of` do not require the same additional disambiguation layer.

This design keeps the dictionary theoretically rich while making parser limitations explicit and auditable.

### Intra-sentential lexical-priming refinement: `while`

During sample validation, several `while` cases were mislabelled as contrastive when they were better interpreted as temporal clauses, especially in patterns such as `while walking`, `while being`, and `while he/she/they...`.

The intra-sentential parser was updated to add lexical-priming/contextual annotations for `while`:

- `while + V-ing` → `temporal_likely`
- `while + subject-like element` → `temporal_likely`
- explicitly contrastive local contexts → `contrastive_likely`

A false-positive filter was also added for nominal time expressions involving `a while`, such as:

- `after a while`
- `for a while`
- `a while ago`

After regeneration, `while` decisions in the 3,000-text sample were:

- `temporal_likely`: 261
- `ambiguous`: 60
- `contrastive_likely`: 12

This supports treating `while` as a multifunctional form requiring parser-level contextual annotation rather than dictionary-level deletion.

### Intra-sentential lexical-priming refinement: `and`

The connector `and` is the largest source of intra-sentential detections and the main source of ambiguity. Manual inspection showed that `and` may link noun phrases, adjective phrases, verb phrases, or full clauses.

The parser therefore adds contextual labels for `and` rather than treating all cases as equally strong clause-level parataxis.

Observed sample labels after refinement:

- `clause_like`: 2,044
- `verb_phrase_like`: 504
- `possibly_clause_like`: 127
- `possibly_phrase_like`: 12,504
- `ambiguous`: 1,242

Inspection showed that `clause_like` cases are generally stronger clause-level candidates, especially where `and` is followed by a pronoun or subject-like element. `verb_phrase_like` cases are also useful as stronger coordination candidates where `and` is followed by an auxiliary or finite verb-like element.

However, `possibly_clause_like`, `possibly_phrase_like`, and `ambiguous` cases remain mixed and include many phrase-level or list-coordination cases.

For strict priming-supported intra-sentential analysis, `and` cases will therefore be retained only when labelled:

- `clause_like`
- `verb_phrase_like`

Other `and` cases are retained in the broad candidate output but excluded from the stricter priming-supported version.

### Intra-sentential lexical-priming refinement: `or`

The connector `or` was inspected because, like `and`, it frequently marks phrase-level or list-level coordination rather than full clause-level parataxis.

In the 3,000-text sample, `or` produced 839 cases:

- `possibly_phrase_like`: 740
- `ambiguous`: 94
- `possibly_clause_like`: 5

Manual inspection showed that most `or` cases involved phrase-level alternation, list alternatives, or short formulaic patterns rather than clear clause-level coordination.

For broad intra-sentential analysis, `or` is retained as an alternation candidate. For strict priming-supported intra-sentential analysis, `or` is excluded for now because reliable clause-level cases are rare in the sample and the small number of possible clause-like cases remains mixed.

### Intra-sentential lexical-priming refinement: `as`

The connector `as` is highly multifunctional and can function as a causal/temporal subordinator, comparative marker, exemplifying marker, or prepositional/role marker.

Sample inspection showed two broad groups:

- `possibly_clause_like`: usually valid hypotactic candidates, e.g. `as we repeated...`, `as he is walking...`, `as there was no food...`
- `ambiguous`: often comparative or role/classification uses, e.g. `as brown as...`, `describe X as...`, `thought of as...`, `not as dangerous...`

Additional filters were added for frequent false-positive patterns:

- `such as`
- `as well` / `as well as`
- role/classification patterns such as `as a/an/the...`

After filtering, `as` cases in the 3,000-text sample were reduced from 1,333 to 1,189.

For strict priming-supported intra-sentential analysis, `as` will be retained only when labelled `possibly_clause_like`. Ambiguous `as` cases remain in the broad candidate output but are excluded from the stricter version.

### Intra-sentential lexical-priming refinement: `so`

The connector `so` is multifunctional. It may function as a result/consequence connector, but it may also occur as an intensifier or adverbial element.

In the 3,000-text sample, `so` produced 1,708 cases:

- `possibly_clause_like`: 804
- `ambiguous`: 904

Manual inspection showed that `possibly_clause_like` cases generally correspond to result/consequence relations, especially when `so` is followed by a subject-like element, e.g. `so he decided...`, `so they...`, `so I...`.

Ambiguous cases included many intensifier or adverbial uses, such as `so many`, `so big`, `not so far`, `so angry`, and `so clearly`.

For broad intra-sentential analysis, all `so` candidates are retained. For strict priming-supported intra-sentential analysis, `so` is retained only when labelled `possibly_clause_like`; ambiguous `so` cases are excluded from the stricter version.

### Intra-sentential lexical-priming refinement: `but`

The connector `but` is generally a reliable adversative marker, but its exact structural scope varies. It may link clauses, verb phrases, or shorter fragments.

In the 3,000-text sample, `but` produced 2,512 cases:

- `possibly_clause_like`: 1,124
- `ambiguous`: 1,388

Manual inspection showed that many ambiguous `but` cases still function as genuine adversative links, but punctuation, learner sentence structure, and fragmentary constructions make their clause-level status less certain.

For broad intra-sentential analysis, all `but` candidates are retained. For strict priming-supported intra-sentential analysis, `but` is retained when labelled `possibly_clause_like`. Ambiguous `but` cases remain available in the broad output and may be inspected separately as an expanded adversative set.

### Intra-sentential lexical-priming refinement: `since`

The connector `since` is multifunctional and may express either temporal meaning or causal/reason meaning. This ambiguity is especially important in L2 writing, where learner use may not always align with native-like distinctions between `since` as a temporal marker and `since` as a causal marker.

In the 3,000-text sample, `since` produced 137 cases:

- `possibly_clause_like`: 89
- `ambiguous`: 34
- `temporal_likely`: 14

Manual inspection showed that `since + explicit time expression` cases are usually temporal, e.g. `since 2005`, `since 2010`, `since then`, and `since that time`.

However, broad patterns such as `since that...` or `since this...` can introduce errors because they may express causal meaning rather than temporal meaning, e.g. `since that child does not belong to him`.

Planned refinement:

- keep `since + year/date/time expression` as `temporal_likely`;
- avoid treating all `since that...` or `since this...` cases as temporal;
- retain clause-like `since` cases as multifunctional candidates rather than forcing them into a single semantic category.

For strict priming-supported intra-sentential analysis, `since` will be retained when labelled `temporal_likely` or `possibly_clause_like`, but its temporal/causal ambiguity will be noted in interpretation.

### Intra-sentential lexical-priming refinement: `when`

The connector `when` is primarily a temporal subordinator, but learner writing contains structurally variable uses, including finite temporal clauses, non-finite clauses, relative-like uses, and punctuation-driven fragments.

In the 3,000-text sample, `when` produced 1,420 cases:

- `possibly_clause_like`: 977
- `ambiguous`: 443

Manual inspection showed that `possibly_clause_like` cases usually represent valid temporal clause candidates, e.g. `when he sees...`, `when I woke up...`, and `when he was 10`.

Ambiguous cases often still have temporal meaning, but their syntactic status is less stable due to learner grammar, punctuation, or non-finite structures, e.g. `when looking...`, `When discovering...`, or fragment-like constructions.

For broad intra-sentential analysis, all `when` candidates are retained. For strict priming-supported intra-sentential analysis, `when` is retained when labelled `possibly_clause_like`; ambiguous cases are retained only in the broad output and treated as lower-confidence temporal candidates.

### Intra-sentential lexical-priming refinement: `then`

The connector `then` is multifunctional. It may mark temporal sequence, conditional consequence, or a looser narrative step.

In the 3,000-text sample, `then` produced 940 cases:

- `possibly_clause_like`: 265
- `ambiguous`: 675

Manual inspection showed that many `then` cases are meaningful temporal or narrative sequencing markers, especially in COREFL narrative-retelling tasks and GiG narrative texts. Some cases also occur in conditional constructions such as `if ... then ...`.

However, many `then` cases are adverbial sequencing markers embedded in lists, fragments, or learner-punctuation structures. These are useful broad sequencing candidates but weaker as strict clause-level evidence.

For broad intra-sentential analysis, all `then` candidates are retained. For strict priming-supported intra-sentential analysis, `then` is retained when labelled `possibly_clause_like`; ambiguous cases remain in the broad output.

### Broad vs priming-supported intra-sentential sample output

After adding the parser-level lexical-priming annotation layer, the 3,000-text intra-sentential sample was regenerated.

The sample produced:

- Broad intra-sentential candidates: 35,515
- Priming-supported candidates: 16,082
- Overall support rate: approximately 45.3%

By corpus:

| Corpus | Broad cases | Priming-supported cases | Support rate |
|---|---:|---:|---:|
| COREFL | 12,888 | 6,275 | 48.7% |
| EFCAMDAT | 4,478 | 1,875 | 41.9% |
| GiG | 18,149 | 7,932 | 43.7% |

The stricter layer retains cases labelled:

- `not_required`
- `clause_like`
- `verb_phrase_like`
- `temporal_likely`
- `contrastive_likely`
- selected `possibly_clause_like` cases for pre-specified multifunctional forms

The stricter layer excludes lower-confidence cases labelled:

- `possibly_phrase_like`
- `ambiguous`

This confirms that the broad intra-sentential regex layer captures many low-confidence coordination and multifunctional cases, while the priming-supported layer provides a more conservative subset for sensitivity analysis.

### Full intra-sentential priming-supported indices

After the full intra-sentential V2 run, a second text-level index file was generated for the priming-supported subset:

- `outputs/v2_intrasentential_full/v2_intrasentential_full_supported_text_indices.csv`

This file contains one row per text and includes raw and per-1,000-word values for supported intra-sentential taxis × macro-category indices.

Broad versus priming-supported mean densities per 1,000 words:

| Corpus | Broad mean / 1,000 | Priming-supported mean / 1,000 |
|---|---:|---:|
| COREFL | 76.40 | 37.91 |
| EFCAMDAT | 57.79 | 22.44 |
| GiG | 62.93 | 27.18 |

The priming-supported layer reduces broad intra-sentential counts substantially, especially because low-confidence phrase/list coordination cases involving forms such as `and`, `or`, `as`, and `so` are excluded from the stricter subset.

However, the broad and priming-supported outputs show the same overall corpus ordering:

`COREFL > GiG > EFCAMDAT`

for mean intra-sentential density per 1,000 words.

This supports using the priming-supported output as a sensitivity analysis for intra-sentential results, while retaining the broad output as the full candidate-detection layer.

### Full inter-sentential supported indices

After adding the inter-sentential marker-confidence annotation layer, a supported text-level index file was generated:

- `outputs/v2_intersentential_full/v2_intersentential_full_supported_text_indices.csv`

This file contains one row per text and includes raw and per-1,000-word values for supported inter-sentential macro-category indices.

Broad versus supported mean densities per 1,000 words:

| Corpus | Broad mean / 1,000 | Supported mean / 1,000 |
|---|---:|---:|
| COREFL | 11.32 | 11.17 |
| EFCAMDAT | 9.05 | 8.71 |
| GiG | 7.98 | 7.91 |

The supported layer excludes low-confidence sentence-initial stance/adverbial items such as `maybe`, `perhaps`, `really`, `never`, `fortunately`, and `unfortunately`. Unlike the intra-sentential parser, the inter-sentential supported layer only slightly reduces total counts because most detected sentence-initial markers are retained.

Supported macro-category means per 1,000 words:

| Corpus | Elaboration | Extension | Enhancement |
|---|---:|---:|---:|
| COREFL | 1.36 | 3.19 | 6.61 |
| EFCAMDAT | 0.93 | 2.62 | 5.16 |
| GiG | 0.62 | 3.18 | 4.10 |

Across all corpora, Enhancement remains the dominant inter-sentential macro category, followed by Extension and Elaboration.

## Summary: tricky multifunctional items and lexical-priming support

The V2 parsers distinguish between dictionary-based candidate detection and parser-level contextual support.

Several connector forms are multifunctional. Their dictionary membership alone does not guarantee that a detected item is functioning as a conjunction or discourse marker in context. For this reason, V2 adds parser-level annotation layers.

### Intra-sentential multifunctionality

The intra-sentential parser is most affected by multifunctional forms because the same surface item may link:

- noun phrases;
- verb phrases;
- clauses;
- comparative expressions;
- temporal frames;
- causal/concessive clauses.

Important problematic forms include:

- `and`
- `or`
- `as`
- `so`
- `while`
- `since`
- `when`
- `then`
- `but`

### Examples of ambiguity

`and` may link noun phrases, verb phrases, or clauses:

- phrase-like: `books and articles`
- verb-phrase-like: `read and write`
- clause-like: `I read the article and I wrote a summary`

`as` may function as a causal/temporal subordinator, comparative marker, or role/classification marker:

- clause-like: `as he walked home`
- comparative/role-like: `as good as`, `described as`, `thought of as`

`so` may function as a result marker or an intensifier:

- result-like: `so he went home`
- intensifier-like: `so tired`, `so many`

`while` may mark temporal simultaneity, contrast, or occur in nominal time expressions:

- temporal: `while walking home`
- contrastive: `while some people agree, others disagree`
- nominal time expression: `after a while`

`since` may be temporal or causal:

- temporal: `since 2010`, `since then`
- causal/reason-like: `since he was tired`

### Lexical-priming/contextual annotation

The intra-sentential parser therefore adds the following columns:

- `is_problematic_multifunctional`
- `priming_decision`
- `priming_confidence`
- `priming_notes`
- `is_priming_supported`

The broad output retains all detected candidates after basic false-positive filtering.

The priming-supported output retains higher-confidence cases, such as:

- clear dictionary items where priming is not required;
- clause-like `and`;
- verb-phrase-like `and`;
- temporal `while`;
- temporal `since`;
- selected clause-like uses of `as`, `so`, `but`, `when`, and `then`.

Lower-confidence cases such as phrase-like coordination, ambiguous `as`, intensifier-like `so`, and broad ambiguous uses are retained in the broad output but excluded from the stricter priming-supported subset.

### Inter-sentential marker-confidence annotation

The inter-sentential parser is less affected by phrase-level ambiguity because it only detects markers at sentence start. However, sentence-initial items may still differ in discourse-marker status.

The inter-sentential parser therefore adds marker-confidence columns:

- `intersentential_marker_type`
- `intersentential_confidence`
- `is_intersentential_supported`
- `intersentential_notes`

The supported inter-sentential subset excludes low-confidence stance/adverbial items such as:

- `maybe`
- `perhaps`
- `really`
- `never`
- `fortunately`
- `unfortunately`

It retains core discourse markers, sequencing markers, conditional/hypotactic frames, and additive/adversative sentence-initial markers.

### Methodological interpretation

The lexical-priming and marker-confidence layers do not claim to perform full syntactic or semantic discourse parsing. Instead, they provide a transparent sensitivity layer between:

`broad dictionary-based candidate detection`

and

`stricter context-supported candidate detection`

This allows the study to report broad position-sensitive conjunction candidates while also checking whether the main corpus-level patterns hold under a more conservative, context-supported operationalisation.

### Full inter-paragraph text-level indices

The full inter-paragraph V2 analysis was run on GiG texts with explicit newline paragraph boundaries.

Eligible texts:

- GiG texts with paragraph boundaries: 2,371

Detected paragraph-initial cases:

- Broad cases: 1,575
- Supported cases: 1,563

A correction was made when generating text-level indices. The first version of the text-level file included only texts with at least one detected inter-paragraph marker, which inflated the mean density. The corrected version includes all eligible GiG texts, including zero-marker texts.

Corrected output file:

- `outputs/v2_interparagraph_full/v2_interparagraph_gig_full_text_indices.csv`

Corrected broad versus supported densities per 1,000 words:

| Corpus | Eligible texts | Broad mean / 1,000 | Broad median / 1,000 | Supported mean / 1,000 | Supported median / 1,000 |
|---|---:|---:|---:|---:|---:|
| GiG | 2,371 | 2.73 | 0.00 | 2.71 | 0.00 |

Supported macro-category means per 1,000 words:

| Macro category | Mean / 1,000 |
|---|---:|
| Elaboration | 0.29 |
| Extension | 0.84 |
| Enhancement | 1.58 |

The median of 0.00 indicates that at least half of eligible GiG texts contain no detected paragraph-initial marker. Inter-paragraph indices should therefore be interpreted as sparse and highly position-dependent.

## Inter-paragraph development checkpoint

### 1. Initial inter-paragraph scope

The first V2 inter-paragraph parser was developed conservatively for GiG only because GiG preserves newline-based paragraph boundaries. The parser detects paragraph-initial discourse markers only when:

- the text contains explicit newline paragraph boundaries;
- the current paragraph is not the first paragraph;
- a dictionary item occurs at the beginning of the paragraph after basic normalisation.

Thus, inter-paragraph detection is position-sensitive:

`paragraph-initial marker + previous paragraph exists`

### 2. Inter-paragraph dictionary audit

The inter-paragraph dictionary was audited using `resources/halliday_paragraph_dict.py`, where the main Hallidayan macro categories are:

- Elaboration
- Extension
- Enhancement

The dictionary contains 1,323 connector-level rows:

| Macro category | Connector-level rows |
|---|---:|
| Extension | 179 |
| Elaboration | 218 |
| Enhancement | 926 |

These workbooks document the full theoretical inventory, not only the operationally retained parser items.

### 3. Marker-confidence layer

A paragraph-level marker-confidence layer was added, parallel to the inter-sentential layer. It classifies paragraph-initial items into types such as:

- high-confidence discourse marker;
- sequential marker;
- conditional or hypotactic frame;
- additive or adversative marker;
- stance or low-confidence adverbial;
- other dictionary marker.

Low-confidence stance/adverbial items are excluded from the supported output but retained in the broad dictionary documentation.

### 4. Full GiG inter-paragraph run

The first full inter-paragraph run was completed for GiG texts with explicit paragraph boundaries.

Results:

| Measure | Value |
|---|---:|
| Eligible GiG texts | 2,371 |
| Broad paragraph-initial cases | 1,575 |
| Supported paragraph-initial cases | 1,563 |

The corrected text-level index file includes zero-marker texts. This correction reduced the mean density from the initially inflated value to the correct value.

Corrected GiG inter-paragraph density:

| Measure | Broad | Supported |
|---|---:|---:|
| Mean per 1,000 words | 2.73 | 2.71 |
| Median per 1,000 words | 0.00 | 0.00 |

The zero median shows that paragraph-initial markers are sparse; many eligible texts contain no detected inter-paragraph marker.

### 5. Outcome package design

A TAACO-style outcome package was generated for the inter-paragraph level:

- `01_diagnostics.xlsx`
- `02_macro_indices.xlsx`
- `03_subcategory_indices.xlsx`
- `04_cases_evidence.xlsx`
- `advanced_connector_indices/connector_indices_extension.xlsx`
- `advanced_connector_indices/connector_indices_elaboration.xlsx`
- `advanced_connector_indices/connector_indices_enhancement.xlsx`

The outcome package separates:

- diagnostics;
- macro-level indices;
- subcategory-level indices;
- case/evidence rows;
- advanced connector-level indices.

This avoids placing all 1,323 connector-level indices in the default output file.

### 6. Denominators

The inter-paragraph outcome files now support three versions of each index:

- raw count;
- per 1,000 words;
- per eligible paragraph start.

Formulas:

`per_1000 = raw_count / word_count_text * 1000`

`per_eligible_paragraph_start = raw_count / (paragraph_count_text - 1)`

The second denominator is important because inter-paragraph markers can only occur at paragraph starts after the first paragraph.

### 7. Index-description workbooks

Three inter-paragraph index-description workbooks were generated:

- `interparagraph_index_description_EXTENSION.xlsx`
- `interparagraph_index_description_ELABORATION.xlsx`
- `interparagraph_index_description_ENHANCEMENT.xlsx`

Each workbook follows the dictionary order from `halliday_paragraph_dict.py`.

Each connector-level row includes:

- Index name;
- In-text name;
- Connector;
- Index description;
- Primary denominator;
- Secondary denominator;
- Support status;
- Dictionary path;
- Output raw column;
- Output per 1,000 column;
- Output per eligible paragraph start column;
- Recommended output file.

The Overview sheets include both logical tab names and actual Excel sheet names because Excel truncates sheet names longer than 31 characters.

### 8. Corpus paragraph-boundary audit

EFCAMDAT was audited for paragraph boundaries and found to have no preserved newline paragraph breaks:

| Corpus | Texts with newline paragraph breaks |
|---|---:|
| EFCAMDAT | 0 |

Therefore, EFCAMDAT is not eligible for inter-paragraph analysis in the current cleaned text field.

COREFL was then audited and found to contain preserved paragraph breaks in a subset of texts:

| Measure | COREFL |
|---|---:|
| Total texts | 3,448 |
| Texts with newline paragraph breaks | 987 |
| Percent eligible | 28.63% |

Sample inspection suggested that many COREFL newline breaks represent genuine paragraph structure, such as narrative stages, plot sections, summaries, and recommendations.

### 9. Updated inter-paragraph corpus decision

The inter-paragraph analysis should now be updated from:

`GiG only`

to:

`GiG + COREFL paragraph-preserved subset`

EFCAMDAT remains excluded from inter-paragraph analysis because paragraph boundaries were not preserved.

Important reporting wording:

- GiG: inter-paragraph analysis uses texts with preserved paragraph boundaries.
- COREFL: inter-paragraph analysis uses the paragraph-preserved subset only.
- EFCAMDAT: excluded from inter-paragraph analysis due to lack of recoverable paragraph boundaries.


## Alignment between index descriptions and inter-paragraph outcome files

The inter-paragraph outputs were designed so that the index-description spreadsheets align directly with the outcome spreadsheets.

### 1. Why outputs were split

The full inter-paragraph dictionary contains 1,323 connector-level rows. If all connector-level indices were placed in one default output file, each connector would require three columns:

- raw count;
- count per 1,000 words;
- count per eligible paragraph start.

This would create approximately:

`1,323 × 3 = 3,969`

connector-level columns, excluding metadata and supported versions. Such a file would be too wide and sparse for most users.

Therefore, the outcome package was split into manageable files:

| Output file | Purpose |
|---|---|
| `01_diagnostics.xlsx` | one row per text; reports whether paragraph-level analysis is possible |
| `02_macro_indices.xlsx` | compact, analysis-ready macro-level indices |
| `03_subcategory_indices.xlsx` | more detailed subcategory-level indices |
| `04_cases_evidence.xlsx` | one row per detected paragraph-initial marker for validation |
| `advanced_connector_indices/connector_indices_extension.xlsx` | advanced connector-level Extension indices |
| `advanced_connector_indices/connector_indices_elaboration.xlsx` | advanced connector-level Elaboration indices |
| `advanced_connector_indices/connector_indices_enhancement.xlsx` | advanced connector-level Enhancement indices |

The default recommended files for most users are:

- `01_diagnostics.xlsx`
- `02_macro_indices.xlsx`
- `03_subcategory_indices.xlsx`
- `04_cases_evidence.xlsx`

The connector-level files are treated as advanced outputs because they are wide and sparse.

### 2. Alignment principle

Each row in the index-description workbooks contains an `Index name`.

That `Index name` is the base name used to generate the corresponding outcome columns.

For each index-description row:

`Index name`

maps to:

- `Index name_raw`
- `Index name_per_1000`
- `Index name_per_eligible_paragraph_start`

Example:

`interparagraph_extension_adversative_but`

maps to:

- `interparagraph_extension_adversative_but_raw`
- `interparagraph_extension_adversative_but_per_1000`
- `interparagraph_extension_adversative_but_per_eligible_paragraph_start`

### 3. Denominator alignment

The index-description workbooks include two denominator columns.

Primary denominator:

`Total words in the text; reported per 1,000 words.`

This corresponds to:

`*_per_1000`

Secondary denominator:

`Eligible paragraph starts, calculated as paragraph_count_text - 1; reported as a rate/proportion of possible paragraph-initial positions.`

This corresponds to:

`*_per_eligible_paragraph_start`

Raw counts correspond to:

`*_raw`

### 4. Recommended output file column

Each index-description row also contains a `Recommended output file` column.

For connector-level rows, this points to one of the advanced connector-level files:

- `advanced_connector_indices/connector_indices_extension.xlsx`
- `advanced_connector_indices/connector_indices_elaboration.xlsx`
- `advanced_connector_indices/connector_indices_enhancement.xlsx`

This allows users to move directly from the index description to the spreadsheet where the corresponding output columns appear.

### 5. Default versus advanced analysis

The macro and subcategory files are the default analysis files because they are compact and interpretable.

The connector-level files are advanced files intended for users who need item-level inspection or highly specific lexical analyses.

Recommended use:

| User goal | Recommended file |
|---|---|
| Check whether texts are eligible for paragraph analysis | `01_diagnostics.xlsx` |
| Run general statistical analyses | `02_macro_indices.xlsx` |
| Analyse Hallidayan subcategories | `03_subcategory_indices.xlsx` |
| Validate detections manually | `04_cases_evidence.xlsx` |
| Inspect individual connectors | `advanced_connector_indices/` |

### 6. Sheet-name alignment

The index-description workbooks are split by macro category and subcategory to keep them manageable.

Because Excel limits sheet names to 31 characters, each Overview sheet contains:

- `Logical tab name`
- `Excel sheet name`

This preserves the full dictionary path while allowing the workbook to remain Excel-compatible.


## Inter-paragraph outcome package validation checkpoint

After updating the inter-paragraph parser and outcome builder, the inter-paragraph pipeline now covers:

`COREFL paragraph-preserved subset + GiG paragraph-preserved subset`

EFCAMDAT remains excluded from inter-paragraph analysis because no newline paragraph boundaries are preserved in the cleaned text field.

### Parser outputs

The updated parser generated combined COREFL + GiG outputs:

- `outputs/v2_interparagraph_full/v2_interparagraph_full_cases.csv`
- `outputs/v2_interparagraph_full/v2_interparagraph_full_text_counts.csv`
- `outputs/v2_interparagraph_full/v2_interparagraph_full_summary.csv`

Summary:

| Corpus | Total texts | Eligible texts with newline boundaries | Detected cases | Cases per eligible text |
|---|---:|---:|---:|---:|
| COREFL | 3,448 | 987 | 673 | 0.6819 |
| GiG | 2,684 | 2,371 | 1,575 | 0.6643 |

Combined:

- Eligible texts: 3,358
- Detected cases: 2,248

### Outcome package

The regenerated TAACO-style outcome package is stored in:

- `outputs/interparagraph_outputs/`

Files:

| File | Rows | Purpose |
|---|---:|---|
| `01_diagnostics.xlsx` | 6,132 | all COREFL + GiG texts; reports eligibility |
| `02_macro_indices.xlsx` | 3,358 | eligible texts only; compact macro-level indices |
| `03_subcategory_indices.xlsx` | 3,358 | eligible texts only; subcategory-level indices |
| `04_cases_evidence.xlsx` | 2,248 | one row per detected paragraph-initial case |
| `advanced_connector_indices/connector_indices_extension.xlsx` | 3,358 | eligible texts only; advanced Extension connector-level indices |
| `advanced_connector_indices/connector_indices_elaboration.xlsx` | 3,358 | eligible texts only; advanced Elaboration connector-level indices |
| `advanced_connector_indices/connector_indices_enhancement.xlsx` | 3,358 | eligible texts only; advanced Enhancement connector-level indices |

### Text-level alignment checks

The final alignment checks passed:

| Check | Result |
|---|---|
| Diagnostics all texts | 6,132 |
| Diagnostics eligible texts | 3,358 |
| Macro rows | 3,358 |
| Subcategory rows | 3,358 |
| Case/evidence rows | 2,248 |
| Macro text IDs equal eligible diagnostic IDs | True |
| Subcategory text IDs equal macro text IDs | True |
| Case text IDs are subset of macro text IDs | True |

Eligible texts by corpus:

| Corpus | Eligible texts |
|---|---:|
| COREFL | 987 |
| GiG | 2,371 |

Case rows by corpus:

| Corpus | Case rows |
|---|---:|
| COREFL | 673 |
| GiG | 1,575 |

### Interpretation note

The inter-paragraph outcome package is now structurally coherent and ready for statistical analysis. However, any COREFL inter-paragraph results should be described as applying to the paragraph-preserved subset only, not the full COREFL corpus.

Recommended wording:

`Inter-paragraph analyses were conducted on texts with recoverable newline-based paragraph boundaries: 987 COREFL texts and 2,371 GiG texts. EFCAMDAT was excluded from paragraph-level analysis because paragraph boundaries were not preserved in the cleaned text field.`

