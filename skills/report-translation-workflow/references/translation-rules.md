# Translation Rules

Apply these rules when translating investor-facing markdown reports.

## Output quality

- Keep the English natural and formal.
- Prefer consistency with past reports when the Japanese meaning matches a repeated pattern.
- Do not make the English more promotional than the source.

## Markdown preservation

- Preserve heading depth.
- Preserve ordered and unordered lists.
- Preserve block quotes, tables, and inline emphasis.
- Keep captions and note markers distinct from body text.

## Factual fidelity

- Do not change names, dates, numbers, percentages, or fund names.
- Keep quoted material clearly separated.
- If the Japanese is ambiguous, prefer the least speculative English and note the ambiguity if it affects meaning.

## Retrieval usage

- `data/knowledge/*.txt` is the first source for repeated stock phrasing.
- `data/knowledge/section_pairs.jsonl` is the second source for section-level bilingual examples.
- Past examples are guidance, not a license to overwrite new-year facts.

## Revision handling

- On targeted feedback, change the smallest necessary span.
- Preserve already accepted terminology elsewhere in the file.
- If the fix should become reusable, update `prompt.md` or `data/knowledge/`.
