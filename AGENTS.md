# AGENTS.md

This file is the short entry point for coding agents. Keep it as a pointer, not a full design document.

## Canonical References

- User-facing overview: `README.md`
- Repository knowledge index: `docs/index.md`
- Architecture map: `docs/ARCHITECTURE.md`
- Operations playbook: `docs/OPERATIONS.md`
- Quality gates: `docs/QUALITY.md`
- Legacy internal notes: `AGENT.md`
- Translation workflow skill: `skills/report-translation-workflow/SKILL.md`
- Memory maintenance skill: `skills/translation-memory-builder/SKILL.md`
- Source cleanup skill: `skills/report-source-preparation/SKILL.md`
- Harness decision record: `docs/adr/0001-harness-guardrails.md`

## Required Checks

Run this before handing work back:

```bash
make check
```

For corpus changes, also inspect the alignment output:

```bash
python3 skills/translation-memory-builder/scripts/validate_corpus_alignment.py \
  --corpus-dir data/past_markdown_files \
  --strict
```

## Working Rules

- Keep `data/past_raw_files/` as immutable source evidence.
- Edit markdown corpus files only when it improves translation or retrieval quality.
- Regenerate `data/knowledge/section_pairs.jsonl` after corpus heading or content cleanup.
- Put reusable translation decisions in `prompt.md` or `data/knowledge/`, not in chat-only notes.
- Add deterministic checks to `scripts/harness_lint.py` when an agent mistake should never repeat.
