# Operations

Use these workflows for recurring repository work.

## Translate A Report

1. Place the Japanese source markdown in `data/past_markdown_files/`.
2. Ask Codex to translate it into `outputs/drafts/`, using `prompt.md`, `data/knowledge/`, and past markdown files as references.
3. Review the draft in `outputs/drafts/`.
4. Move accepted deliverables to `outputs/final/` when ready.
5. Run `make check`.

## Convert Word Source To Markdown

1. Put the source `.docx` in `data/past_raw_files/`.
2. Run:

```bash
python3 skills/report-source-preparation/scripts/convert_docx_to_markdown.py \
  "Unison Impact_J_2024.docx"
```

3. Review the generated markdown in `data/past_markdown_files/`.
4. Run `make check`.

## Export Markdown To Word

1. Review the English draft in `outputs/drafts/`.
2. Run:

```bash
python3 skills/report-docx-export/scripts/export_markdown_to_docx.py \
  "outputs/drafts/Unison Impact_E_2024.md"
```

3. Use the `.docx` in `outputs/final/` as the Word deliverable.
4. Run `make check`.

Debug prompts or review notes may be written to `outputs/prompts/` when needed.

## Refresh Translation Memory

1. Inspect alignment:

```bash
python3 skills/translation-memory-builder/scripts/validate_corpus_alignment.py \
  --corpus-dir data/past_markdown_files \
  --strict
```

2. Fix markdown corpus structure if needed.
3. Regenerate memory:

```bash
python3 skills/translation-memory-builder/scripts/extract_section_pairs.py \
  --corpus-dir data/past_markdown_files \
  --output data/knowledge/section_pairs.jsonl
```

4. Refresh generated docs:

```bash
python3 scripts/refresh_generated_docs.py
```

5. Run `make check`.

## Add Harness Knowledge

- Put stable decisions in `docs/adr/`.
- Put operational workflows here.
- Put generated summaries in `docs/generated/` through `scripts/refresh_generated_docs.py`.
- Add repeated failure prevention to `scripts/harness_lint.py`.
