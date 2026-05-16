#!/usr/bin/env python3
"""Project-specific deterministic checks for coding-agent work."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_AGENT_POINTER_LINES = 50
MAX_SKILL_LINES = 500
ROOT_MARKDOWN_ALLOWLIST = {
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "prompt.md",
}
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
}


@dataclass(frozen=True)
class Violation:
    path: Path
    message: str
    fix: str

    def render(self) -> str:
        rel_path = self.path.relative_to(ROOT)
        return f"{rel_path}: {self.message}\n  fix: {self.fix}"


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def check_generated_artifacts(files: list[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in files:
        if path.suffix == ".pyc" or "__pycache__" in path.parts:
            violations.append(
                Violation(
                    path=path,
                    message="Generated Python cache is present in the repository tree. [ADR-0001]",
                    fix="Run `make clean-pycache` and keep cache files ignored.",
                )
            )
        if path.name == ".DS_Store":
            violations.append(
                Violation(
                    path=path,
                    message="macOS metadata file is present in the repository tree. [ADR-0001]",
                    fix="Remove the `.DS_Store` file and keep it ignored.",
                )
            )
    return violations


def check_root_markdown_outputs(files: list[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in files:
        if path.parent != ROOT or path.suffix.lower() != ".md":
            continue
        if path.name in ROOT_MARKDOWN_ALLOWLIST:
            continue
        violations.append(
            Violation(
                path=path,
                message="Markdown output artifact is not allowed at repository root. [ADR-0001]",
                fix="Move translation drafts to `outputs/drafts/`, accepted deliverables to `outputs/final/`, or make the file an explicit docs source.",
            )
        )
    return violations


def check_generated_docs() -> list[Violation]:
    script = ROOT / "scripts" / "refresh_generated_docs.py"
    generated_dir = ROOT / "docs" / "generated"
    if not script.exists():
        return [
            Violation(
                path=script,
                message="Generated docs checker is missing. [ADR-0001]",
                fix="Restore `scripts/refresh_generated_docs.py` so `docs/generated/` has a source of truth.",
            )
        ]

    result = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return []

    details = " ".join(line.strip() for line in result.stderr.splitlines() if line.strip())
    return [
        Violation(
            path=generated_dir,
            message=f"`docs/generated/` is stale or contains hand-written files. {details} [ADR-0001]",
            fix="Run `python3 scripts/refresh_generated_docs.py` and commit the generated changes.",
        )
    ]


def check_agent_pointer(name: str) -> list[Violation]:
    path = ROOT / name
    if not path.exists():
        return [
            Violation(
                path=path,
                message=f"{name} is missing. [ADR-0001]",
                fix="Create a short pointer file that references canonical docs and `make check`.",
            )
        ]

    lines = path.read_text(encoding="utf-8").splitlines()
    violations: list[Violation] = []
    if len(lines) > MAX_AGENT_POINTER_LINES:
        violations.append(
            Violation(
                path=path,
                message=f"{name} has {len(lines)} lines; agent entry points must stay under {MAX_AGENT_POINTER_LINES}. [ADR-0001]",
                fix="Move detailed instructions into canonical docs, skills, tests, or ADRs.",
            )
        )

    text = "\n".join(lines)
    required_patterns = {
        "AGENTS.md": ["README.md", "docs/index.md", "make check", "skills/", "docs/adr/0001-harness-guardrails.md"],
        "CLAUDE.md": ["AGENTS.md", "make check"],
    }[name]
    for pattern in required_patterns:
        if pattern not in text:
            violations.append(
                Violation(
                    path=path,
                    message=f"{name} does not point to `{pattern}`. [ADR-0001]",
                    fix=f"Add `{pattern}` as a pointer instead of duplicating its contents.",
                )
            )

    return violations


def check_skill_frontmatter(files: list[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in files:
        if path.name != "SKILL.md" or "skills" not in path.parts:
            continue

        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) > MAX_SKILL_LINES:
            violations.append(
                Violation(
                    path=path,
                    message=f"Skill body has {len(lines)} lines; keep SKILL.md under {MAX_SKILL_LINES} lines.",
                    fix="Move detailed examples or reference material into `references/` and link to them conditionally.",
                )
            )

        match = re.match(r"^---\n(?P<body>.*?)\n---\n", text, flags=re.DOTALL)
        if not match:
            violations.append(
                Violation(
                    path=path,
                    message="Skill file is missing YAML-style frontmatter.",
                    fix="Start the file with `---`, then include `name:` and `description:`.",
                )
            )
            continue

        frontmatter = match.group("body")
        for key in ("name:", "description:"):
            if key not in frontmatter:
                violations.append(
                    Violation(
                        path=path,
                        message=f"Skill frontmatter is missing `{key}`.",
                        fix=f"Add `{key}` to the frontmatter so agents can discover the skill reliably.",
                    )
                )
    return violations


def check_skill_agent_metadata(files: list[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for skill_path in files:
        if skill_path.name != "SKILL.md" or "skills" not in skill_path.parts:
            continue

        skill_dir = skill_path.parent
        metadata_path = skill_dir / "agents" / "openai.yaml"
        if not metadata_path.exists():
            violations.append(
                Violation(
                    path=skill_path,
                    message="Skill is missing `agents/openai.yaml` UI metadata.",
                    fix="Add display_name, short_description, and default_prompt metadata for discoverability.",
                )
            )
            continue

        metadata = metadata_path.read_text(encoding="utf-8")
        for key in ("display_name:", "short_description:", "default_prompt:"):
            if key not in metadata:
                violations.append(
                    Violation(
                        path=metadata_path,
                        message=f"Skill agent metadata is missing `{key}`.",
                        fix=f"Add `{key}` so the skill is understandable in UI surfaces.",
                    )
                )
    return violations


def check_python_parse(files: list[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in files:
        if path.suffix != ".py":
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            violations.append(
                Violation(
                    path=path,
                    message=f"Python syntax error at line {exc.lineno}: {exc.msg}",
                    fix="Fix the syntax error before running translation or memory commands.",
                )
            )
    return violations


def check_jsonl_memory() -> list[Violation]:
    path = ROOT / "data" / "knowledge" / "section_pairs.jsonl"
    if not path.exists():
        return [
            Violation(
                path=path,
                message="Translation memory JSONL file is missing.",
                fix="Run `python3 skills/translation-memory-builder/scripts/extract_section_pairs.py --corpus-dir data/past_markdown_files --output data/knowledge/section_pairs.jsonl`.",
            )
        ]

    violations: list[Violation] = []
    required_keys = {"jp_file", "en_file", "jp_heading", "en_heading", "jp_text", "en_text", "labels"}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            violations.append(
                Violation(
                    path=path,
                    message=f"Invalid JSONL at line {line_no}: {exc.msg}",
                    fix="Regenerate the translation memory from the aligned markdown corpus.",
                )
            )
            continue

        missing = sorted(required_keys - set(record))
        if missing:
            violations.append(
                Violation(
                    path=path,
                    message=f"Record at line {line_no} is missing keys: {', '.join(missing)}",
                    fix="Regenerate the memory file so retrieval has the expected schema.",
                )
            )
    return violations


def main() -> int:
    files = iter_files()
    violations: list[Violation] = []
    violations.extend(check_generated_artifacts(files))
    violations.extend(check_root_markdown_outputs(files))
    violations.extend(check_agent_pointer("AGENTS.md"))
    violations.extend(check_agent_pointer("CLAUDE.md"))
    violations.extend(check_generated_docs())
    violations.extend(check_skill_frontmatter(files))
    violations.extend(check_skill_agent_metadata(files))
    violations.extend(check_python_parse(files))
    violations.extend(check_jsonl_memory())

    if violations:
        print("Harness lint failed. Fix these deterministic issues:\n", file=sys.stderr)
        for violation in violations:
            print(violation.render(), file=sys.stderr)
        return 1

    print("Harness lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
