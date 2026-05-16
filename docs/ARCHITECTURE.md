# Architecture

This repository supports section-based Japanese-to-English report translation with reusable bilingual memory.

## Top-Level Boundaries

- `src/`: production runners for translation execution
- `scripts/`: deterministic repository maintenance and harness tooling
- `skills/`: agent workflows with bundled scripts and references
- `data/past_raw_files/`: immutable source evidence
- `data/past_markdown_files/`: normalized bilingual markdown corpus
- `data/knowledge/`: curated reusable knowledge and generated section memory
- `outputs/`: translation drafts, final deliverables, and debug prompts
- `docs/`: repository knowledge, decisions, plans, and generated indexes

## Data Flow

1. Raw reports are preserved in `data/past_raw_files/`.
2. Clean markdown corpus files live in `data/past_markdown_files/`.
3. `skills/translation-memory-builder/scripts/extract_section_pairs.py` builds `data/knowledge/section_pairs.jsonl`.
4. `skills/report-translation-workflow/scripts/prepare_translation_prompt.py` assembles section prompts from source context, curated knowledge, and bilingual examples.
5. `src/translate_report.py` writes English drafts to `outputs/drafts/` unless `--output` is provided.
6. `skills/report-docx-export/scripts/export_markdown_to_docx.py` exports reviewed markdown to `outputs/final/`.

## Generated Knowledge

Files in `docs/generated/` are derived from repository state by `scripts/refresh_generated_docs.py`. Update the source data or the generator, then regenerate; do not hand-edit generated files.
