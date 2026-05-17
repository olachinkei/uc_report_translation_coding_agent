---
name: report-source-preparation
description: Use this skill when a new Word or markdown report should be copied or converted into a Japanese .md file for translation preparation.
---

# Report Source Preparation

Use this skill for the ingestion path: source document in, Japanese markdown file out.

## When To Use It

- the user asks to change a source report into an md file
- the user provides a new `.docx` report
- the user provides an existing `.md` report that should be copied into `data/past_markdown_files/`

## Workflow

### 1. Preserve the source file

- keep the original file untouched
- create the `.md` file in `data/past_markdown_files/`

### 2. Create the markdown file

- use the bundled script
- when the source is `.md`, the script copies it
- when the source is `.docx`, the script converts it to markdown with pandoc
- preserve paragraph order, lists, block quotes, tables, and dates
- extract media only when the user needs images carried forward

```bash
python3 skills/report-source-preparation/scripts/convert_docx_to_markdown.py \
  "Unison Impact_J_2024.docx" \
  --overwrite
```

Default output is `data/past_markdown_files/<source-stem>.md`.

### 3. Check heading structure only when needed

- identify true chapter and section titles from Word layout cues
- convert them into markdown headings
- avoid promoting ordinary emphasized sentences into headings

Typical heading candidates in this project:

- ごあいさつ
- ESG framework overview
- quantification / methodology sections
- case study section titles
- 編集後記

### 4. Remove only translation-blocking noise when needed

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
- The script requires `pandoc` only when the source is `.docx`.
