---
name: report-translation-workflow
description: Use this skill when translating a new Japanese markdown report into English while reusing past bilingual report examples, preserving markdown headings, and iterating on specific sections based on user feedback.
---

# Report Translation Workflow

Use this skill for the production path: new Japanese markdown in, English markdown out.

## Inputs To Confirm

- `prompt.md`: base translation prompt and built-in dictionary
- `data/past_markdown_files/`: place the source Japanese markdown here and keep the bilingual corpus here
- `data/knowledge/`: reusable stock phrasing such as greetings, framework explanations, and afterword language
- the new Japanese markdown file to translate

If `data/knowledge/section_pairs.jsonl` does not exist or looks stale after data updates, first use `$translation-memory-builder`.

## Translation Workflow

### 1. Inspect and segment the source file

- Parse the markdown into sections by heading.
- Analyze each section before translating it. Identify:
  - the section label and likely reusable wording
  - all names, dates, years, percentages, counts, fund names, and company names
  - quotations, captions, tables, note markers, and markdown that must remain distinct
- Keep heading depth exactly as written in the source unless the user explicitly asks for restructuring.
- Classify each section before translating. Useful labels in this project are:
  - `greeting`
  - `framework`
  - `quantification`
  - `case-study`
  - `timeline`
  - `quote`
  - `caption`
  - `afterword`

When a section contains subheadings, translate it subsection by subsection instead of flattening it.

### 2. Retrieve reusable examples before translating

- Search `data/knowledge/` first for stable wording that should stay consistent across years.
- Include the relevant or similar `.txt` knowledge content in the translation prompt for each section. For example, the `greeting` section must include `data/knowledge/1_greeting.txt` when available.
- Search the bilingual markdown corpus next. Do not put the whole `data/knowledge/section_pairs.jsonl` file into the prompt; use the prompt preparation script's lightweight token index to retrieve a small candidate set, then include only the top section pairs.
- `section_pairs.jsonl` starts with `record_type: "heading_translation"` records. Treat these as the preferred source for heading translations, then use section-pair records for body phrasing.
- Prefer retrieving 1-3 high-confidence examples per section instead of flooding the prompt.
- Use `scripts/prepare_translation_prompt.py` to assemble:
  - surrounding context
  - reusable curated knowledge snippets
  - the current Japanese section
  - top bilingual examples from past reports
  - the base prompt template from `prompt.md`

If no strong examples are found, continue with translation and note that the section was translated without a close precedent.

## Suggested helper commands

```bash
python3 skills/report-translation-workflow/scripts/prepare_translation_prompt.py \
  --source-md path/to/new_report.md \
  --section "ごあいさつ" \
  --template prompt.md \
  --memory-file data/knowledge/section_pairs.jsonl \
  --knowledge-dir data/knowledge \
  --candidate-limit 25
```

```bash
python3 skills/report-translation-workflow/scripts/prepare_translation_prompt.py \
  --source-md data/past_markdown_files/Unison\ Impact_J_2024.md \
  --section "ごあいさつ" \
  --template prompt.md \
  --memory-file data/knowledge/section_pairs.jsonl \
  --knowledge-dir data/knowledge \
  --output outputs/prompts/greeting.prompt.md
```

### 3. Translate section by section

- Preserve markdown structure, list markers, block quotes, tables, and inline emphasis.
- Preserve company names, fund names, years, dates, percentages, and numbers exactly unless the source is clearly inconsistent.
- Keep an investor-facing tone: clear, formal, and natural, not word-for-word literal.
- Reuse stable phrasing from past reports when the meaning is genuinely the same.
- Do not force reuse if the new year changes the substance.
- Non-negotiable recurring wording:
  - Translate the greeting opener `投資家の皆さま` exactly as `To our valued investors,`.
  - Never use `Dear Investors,`.
  - Translate `ごあいさつ` as `Greeting` unless the user explicitly requests another heading.

### 4. Validate and review

Run a validation loop before finalizing:

1. Review the translated section against the source line by line.
2. Check for accidental summarization, omitted facts, missing sentences, number/name drift, and markdown breakage.
3. If omissions or over-summarization are found, retranslate the affected section before moving on.
4. Run `make check`.
5. Repeat until the review and deterministic checks pass.

Check every translated section for:

- omitted facts
- accidental summarization or compression of source content
- changed numbers or dates
- mistranslated proper nouns
- broken markdown structure
- headings that became less specific than the source
- quotes or captions that were accidentally normalized into body text

When the file is long, review in this order:

1. headings and section order
2. names, dates, metrics, and fund references
3. natural English flow

### 5. Handle user corrections surgically

When the user says "change this paragraph" or "make this sentence softer":

- edit only the targeted section and the minimum adjacent text needed for coherence
- do not retranslate unaffected sections
- preserve terminology choices already accepted elsewhere in the document
- if a requested change should become a reusable pattern, also suggest updating `data/knowledge/` or the dictionary section in `prompt.md`

## Gotchas

- Keep the Japanese source untouched unless the user explicitly asks for cleanup.
- Do not flood prompts with examples. Default to 1-3 high-confidence bilingual examples.
- Do not retranslate accepted sections when the user asks for a localized correction.
- Do not store one-off case-study facts in `data/knowledge/`; use the corpus for those.

## Output Conventions

- Source Japanese markdown should live in `data/past_markdown_files/`.
- The default English draft output is written to `outputs/drafts/`.
- If the source file name contains `_J_`, the default top-level output name replaces it with `_E_`.
- If a side-by-side review UI exists, open it after writing the English output and use subsequent feedback to patch the translation in place.

## References

- Translation style and guardrails: `references/translation-rules.md`
- Prompt assembly helper: `scripts/prepare_translation_prompt.py`
