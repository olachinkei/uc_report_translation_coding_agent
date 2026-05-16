---
name: report-source-preparation
description: Use this skill when a new Word or markdown report needs to be converted into clean Japanese markdown with reliable heading structure before translation.
---

# Report Source Preparation

Use this skill for the ingestion path: raw source document in, translation-ready Japanese markdown out.

## When To Use It

- the user provides a new `.docx` report
- the user provides a rough markdown export with weak heading structure
- Word-origin artifacts are interfering with section-based translation

## Workflow

### 1. Preserve the source

- keep the original `.docx` untouched
- write cleaned markdown into `data/past_markdown_files/`

### 2. Convert into markdown

- use the bundled script when the source is `.docx`
- preserve paragraph order, lists, block quotes, tables, and dates
- extract media only when the user needs images carried forward

```bash
python3 skills/report-source-preparation/scripts/convert_docx_to_markdown.py \
  "Unison Impact_J_2024.docx" \
  --overwrite
```

Default output is `data/past_markdown_files/<source-stem>.md`.

### 3. Rebuild heading structure

- identify true chapter and section titles from Word layout cues
- convert them into markdown headings
- avoid promoting ordinary emphasized sentences into headings

Typical heading candidates in this project:

- ごあいさつ
- ESG framework overview
- quantification / methodology sections
- case study section titles
- 編集後記

### 4. Remove only translation-blocking noise

- remove empty headings
- clean obvious Word artifacts such as isolated underline tags
- keep meaningful notes, captions, and quoted text

### 5. Final source checks

Validation loop:

1. Clean the source markdown.
2. Verify the checklist below.
3. Run `make check`.
4. Fix any deterministic failure before handing off to `$report-translation-workflow`.

Checklist:

- heading depth is consistent
- each major chapter is a standalone markdown section
- numbers, dates, and company names survived conversion
- the file can be translated section by section without manual reconstruction
- the cleaned source markdown now lives in `data/past_markdown_files/`

## Gotchas

- Do not edit files in `data/past_raw_files/`; they are source evidence.
- Do not translate content in this skill. Produce translation-ready Japanese markdown only.
- Remove only artifacts that block section parsing or translation. Keep meaningful captions, notes, quotes, and tables.
- The conversion script requires `pandoc`.
