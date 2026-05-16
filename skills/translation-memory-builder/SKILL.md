---
name: translation-memory-builder
description: Use this skill when adding or refreshing past bilingual report data, extracting aligned Japanese-English section pairs, and updating reusable knowledge files that support future report translation.
---

# Translation Memory Builder

Use this skill for the offline preparation path: maintain the reusable memory that future translations depend on.

## When To Use It

- new past report pairs were added to `data/past_raw_files/` or `data/past_markdown_files/`
- headings were cleaned up in past markdown files
- reusable examples in `data/knowledge/` need to be refreshed
- retrieval quality has dropped and the section-pair index should be rebuilt

## Workflow

### 1. Confirm the corpus layout

- Japanese and English markdown files should live in `data/past_markdown_files/`
- file names should pair cleanly by year and language, for example:
  - `Unison Impact_J_2024.md`
  - `Unison Impact_E_2024.md`
- raw Word files should remain in `data/past_raw_files/` for traceability

If a Japanese file has no English counterpart, keep it in the corpus but exclude it from the aligned memory index until a pair exists.

### 2. Normalize only what helps retrieval

- add or fix markdown headings when section boundaries are obvious
- remove Word artifacts only when they interfere with search or prompt assembly
- do not rewrite historical content just to make the English read better

The goal is retrieval quality, not retrospective editing.

### 3. Extract aligned section pairs

Build `data/knowledge/section_pairs.jsonl` from the bilingual markdown corpus.

Plan-validate-execute:

1. Inspect alignment gaps:

```bash
python3 skills/translation-memory-builder/scripts/validate_corpus_alignment.py \
  --corpus-dir data/past_markdown_files \
  --strict
```

2. Fix heading or noise issues in the markdown corpus if alignment fails.
3. Rebuild memory:

```bash
python3 skills/translation-memory-builder/scripts/extract_section_pairs.py \
  --corpus-dir data/past_markdown_files \
  --output data/knowledge/section_pairs.jsonl
```

4. Run the repository gate:

```bash
make check
```

The script aligns sections by file pair and section order. It writes searchable `record_type: "heading_translation"` records at the top of `section_pairs.jsonl`, followed by full section-pair records. Review mismatches manually when one side contains extra headings or formatting artifacts.

### 4. Curate reusable knowledge files

Update `data/knowledge/*.txt` only with content that is stable and repeatedly useful, such as:

- greetings
- firm-level ESG framework descriptions
- quantification methodology explanations
- recurring afterword language

Avoid putting one-off case-study details into reusable knowledge files unless they express a recurring translation pattern.

### 5. Refresh the prompt dictionary when needed

If a term should always map to the same English, add it to the dictionary section inside `prompt.md`.

Good candidates:

- company names
- fund names
- branded frameworks
- recurring product or project names

## Review Checklist

Before considering the memory update done, verify:

- each Japanese file has the expected English partner
- section headings are useful enough to drive retrieval
- the top of `section_pairs.jsonl` contains searchable heading translation records
- `section_pairs.jsonl` contains high-signal sections instead of giant unsegmented blobs
- `data/knowledge/*.txt` contains stable phrasing, not year-specific noise
- `prompt.md` dictionary additions are actually recurring terms

## Gotchas

- `section_pairs.jsonl` is generated data. Edit corpus markdown or extraction logic, then regenerate it.
- Do not add a Japanese file to aligned memory until its English counterpart exists.
- Raw Word files stay untouched; normalize only markdown corpus files.

## References

- Knowledge curation rules: `references/knowledge-selection.md`
- Pair extraction helper: `scripts/extract_section_pairs.py`
- Alignment checker: `scripts/validate_corpus_alignment.py`
