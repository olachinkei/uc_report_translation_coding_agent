#!/usr/bin/env python3
"""Convert a source Word docx report into markdown for translation preparation."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "past_raw_files"
MARKDOWN_DIR = ROOT / "data" / "past_markdown_files"


def require_suffix(path: Path, suffix: str, role: str) -> None:
    if path.suffix.lower() != suffix:
        raise SystemExit(f"{role} must be a `{suffix}` file: {path}")


def ensure_output_available(output_path: Path, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        raise SystemExit(f"Output already exists: {output_path}. Use --overwrite to replace it.")


def require_pandoc() -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("pandoc is required. Install pandoc before converting docx to markdown.")
    return pandoc


def resolve_docx_path(raw_source: str) -> Path:
    candidate = Path(raw_source)
    if candidate.is_absolute() and candidate.exists():
        require_suffix(candidate, ".docx", "Source")
        return candidate

    direct = ROOT / raw_source
    if direct.exists():
        require_suffix(direct, ".docx", "Source")
        return direct

    raw_candidate = RAW_DIR / raw_source
    if raw_candidate.exists():
        require_suffix(raw_candidate, ".docx", "Source")
        return raw_candidate

    raise SystemExit(f"Source docx not found: {raw_source}")


def default_output_path(source_path: Path) -> Path:
    return MARKDOWN_DIR / f"{source_path.stem}.md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source .docx path or filename in data/past_raw_files/.")
    parser.add_argument("--output", type=Path, help="Output markdown path. Defaults to data/past_markdown_files/.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    pandoc = require_pandoc()
    source_path = resolve_docx_path(args.source)
    output_path = args.output or default_output_path(source_path)

    require_suffix(output_path, ".md", "Output")
    ensure_output_available(output_path, args.overwrite)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            pandoc,
            str(source_path),
            "--from",
            "docx",
            "--to",
            "gfm",
            "--wrap",
            "none",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
    )
    print(f"Wrote markdown to {output_path}")


if __name__ == "__main__":
    main()
