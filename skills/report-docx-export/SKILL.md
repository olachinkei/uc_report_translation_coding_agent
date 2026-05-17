---
name: report-docx-export
description: Use this skill when the user asks to create, convert, export, or generate a Word .docx file from a markdown .md report, especially translated reports moving from outputs/drafts/ to outputs/final/.
---

# Report DOCX Export

Use this skill for the delivery path: reviewed markdown in, Word `.docx` out.
When the user gives only a short request such as "$report-docx-export を使って、outputs/drafts/Unison Impact_E_2025.md を Wordファイルに変換して", infer the standard output path and finish the export without asking for boilerplate.

## When To Use It

- the user asks to create a Word file from markdown, for example ".mdからdocxを作って"
- the English markdown draft has been reviewed
- a final deliverable should be written to `outputs/final/`

## Defaults To Infer

- Use the markdown path named in the user request as the source.
- Write the Word file to `outputs/final/<source-stem>.docx`.
  - Example: `outputs/drafts/Unison Impact_E_2025.md` -> `outputs/final/Unison Impact_E_2025.docx`
- Use `--overwrite` for the normal regenerated deliverable path.
- After exporting, verify that the `.docx` exists and run `make check`.

## Workflow

### 1. Confirm the source markdown

- Prefer reviewed files in `outputs/drafts/`.
- Use `outputs/final/` only when re-exporting an accepted final markdown.
- Do not export directly from Japanese source markdown unless the user explicitly asks.

### 2. Export with the bundled script

For the normal path, run:

```bash
python3 skills/report-docx-export/scripts/export_markdown_to_docx.py \
  "outputs/drafts/Unison Impact_E_2024.md" \
  --overwrite
```

Default output is `outputs/final/<source-stem>.docx`, so the user does not need to specify it.

For an explicit output path, run:

```bash
python3 skills/report-docx-export/scripts/export_markdown_to_docx.py \
  "outputs/drafts/Unison Impact_E_2024.md" \
  --output "outputs/final/Unison Impact_E_2024.docx" \
  --overwrite
```

For Word styling based on an existing document, add:

```bash
--reference-doc path/to/reference.docx
```

### 3. Validate

Run:

```bash
make check
```

Then open or inspect the `.docx` if visual layout quality matters.

## Gotchas

- This script requires `pandoc`.
- If `pandoc` is missing, report that dependency clearly instead of hand-writing a converter.
- Treat `.docx` as an export artifact. Keep the reviewed markdown as the editable source of truth.
- If the Word layout needs brand-specific styling, provide a reference `.docx` and pass it with `--reference-doc`.
- Do not overwrite an existing `.docx` unless the user asked for replacement or `--overwrite` is appropriate for a regenerated artifact.
