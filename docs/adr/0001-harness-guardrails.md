# ADR 0001: Harness Guardrails

- Status: Accepted
- Date: 2026-05-16

## Context

This repository is operated by coding agents and humans. Translation quality depends on a clean bilingual corpus, stable prompt assets, and small Python utilities. Free-form instructions alone are too easy to skip or misread.

## Decision

We will keep agent instructions short and pointer-based in `AGENTS.md` and `CLAUDE.md`. Repository quality is enforced by deterministic commands:

- `make lint` runs `scripts/harness_lint.py`
- `make test` compiles Python sources
- `make alignment` validates bilingual corpus section alignment
- `make check` runs the full local gate

When a repeated agent failure appears, add a deterministic rule to `scripts/harness_lint.py` or a focused test instead of adding more prose.

## Consequences

Agents get a fast, explicit completion gate. Project-specific constraints such as raw file immutability, corpus alignment, and generated file hygiene can be checked without relying on model judgment.
