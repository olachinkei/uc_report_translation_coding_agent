---
name: report-docx-export
description: Use this skill when exporting a translated markdown report into a Word .docx deliverable, usually from outputs/drafts/ to outputs/final/.
---

# Report DOCX Export

Use this skill for the delivery path: reviewed English markdown in, Word `.docx` out.

## When To Use It

- the English markdown draft has been reviewed
- the user asks to create a Word file from markdown
- a final deliverable should be written to `outputs/final/`

## Workflow

### 1. Confirm the source markdown

- Prefer reviewed files in `outputs/drafts/`.
- Use `outputs/final/` only when re-exporting an accepted final markdown.
- Do not export directly from Japanese source markdown unless the user explicitly asks.

### 2. Export with the bundled script

```bash
python3 skills/report-docx-export/scripts/export_markdown_to_docx.py \
  "outputs/drafts/Unison Impact_E_2024.md" \
  --overwrite
```

Default output is `outputs/final/<source-stem>.docx`.

### 3. Validate

Run:

```bash
make check
```

Then open or inspect the `.docx` if visual layout quality matters.

## Gotchas

- This script requires `pandoc`.
- Treat `.docx` as an export artifact. Keep the reviewed markdown as the editable source of truth.
- If the Word layout needs brand-specific styling, provide a reference `.docx` and pass it with `--reference-doc`.
