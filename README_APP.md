What ConjuncTool does
How to install requirements
How to run intra / intersent / interpara
Important limitation: interpara requires real paragraph breaks
Output description

# ConjuncTool App

ConjuncTool is a small research prototype for detecting Halliday-based conjunction patterns in English texts.

It currently supports three V2 analysis levels:

1. **Intra-sentential conjunctions**  
   Detects conjunctions inside sentences, including broad paratactic and hypotactic relations.

2. **Inter-sentential conjunctions**  
   Detects discourse markers at the beginning of sentences, where a previous sentence exists.

3. **Inter-paragraph conjunctions**  
   Detects discourse markers at the beginning of paragraphs, where a previous paragraph exists.

## Important note

The inter-paragraph parser requires real paragraph boundaries.

Formula:

`real newline paragraph breaks = valid inter-paragraph analysis`

If a text has no paragraph breaks, the inter-paragraph parser will return no cases.

## Install requirements

From the app folder:

```bash
cd ~/conjunctool_app
pip install -r requirements.txt
```

## GUI prototype milestone

The current ConjuncTool V2 prototype includes a working Tkinter GUI.

Implemented GUI functions:

- select an input `.txt` file;
- choose analysis level:
  - `intra`
  - `intersent`
  - `interpara`
- run analysis;
- export results to CSV;
- open the output CSV directly from the app.

The GUI calls the same V2 parser modules used by the command-line runner:

- `app/parsers/intra_v2.py`
- `app/parsers/intersent_v2.py`
- `app/parsers/interpara_v2.py`

Current status:

`GUI → parser → CSV export → open output file = working`

Next planned feature:

`summary output by detected item, macro category, and taxis`

## Current Stable Milestone: V2 Ambiguity Filters

The current app version includes the validated V2 ambiguity-filter milestone.

Implemented and tested filters:

- `rather`: excludes degree-adverb uses while retaining `rather than`
- `once + adjective`: excludes formerly/previously uses such as `once strong`
- `while` noun phrases: excludes period-of-time uses such as `for a while`
- `once in a while`: excludes the frequency idiom

Research-audited items requiring no app patch at this stage:

- `so`
- `still`
- `yet`
- `since`
- `then`
- `as`
- `for`
- `like`
- `only`

Latest stable app checkpoint:

`checkpoints/app_v2_ambiguity_filter_milestone_stable_20260505_1550`

