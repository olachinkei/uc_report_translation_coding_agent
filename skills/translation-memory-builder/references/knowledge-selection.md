# Knowledge Selection

Use this reference when deciding what belongs in `data/knowledge/` and what should stay only in the historical corpus.

## Good candidates

- greetings that recur every year
- house style around ESG or impact-investing explanations
- recurring descriptions of frameworks, assessment methods, and governance philosophy
- afterword language and reader feedback requests

## Bad candidates

- year-specific portfolio case-study details
- figures, dates, or milestones that change every year
- captions that only make sense for a single report layout
- long passages kept only because the English sounds polished

## Editing principle

`data/knowledge/` should stay small and high signal.

If a passage is useful because of a translation pattern but too specific to paste verbatim, keep it in `section_pairs.jsonl` instead of a curated `.txt` file.
