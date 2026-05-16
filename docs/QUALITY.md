# Quality

Quality is enforced by deterministic checks before agent or human judgment.

## Required Gate

```bash
make check
```

This runs:

- `scripts/harness_lint.py`
- Python syntax compilation for `src/`, `skills/`, and `scripts/`
- bilingual corpus alignment validation

## Harness Invariants

- `AGENTS.md` and `CLAUDE.md` stay short and pointer-based.
- Skill files must have frontmatter and `agents/openai.yaml` metadata.
- Generated cache files and `.DS_Store` files are not allowed.
- Translation output markdown does not live at repository root.
- `docs/generated/` must match `scripts/refresh_generated_docs.py --check`.
- `make check` must not require an OpenAI API key.

## Translation Quality

Review translated output for:

- preserved numbers, dates, company names, fund names, and proper nouns
- unchanged markdown structure unless explicitly requested
- no omitted facts
- investor-facing English that reuses stable recurring phrasing when appropriate

Recurring translation decisions belong in `prompt.md` or `data/knowledge/`, not in chat-only notes.
