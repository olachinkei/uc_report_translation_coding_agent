#!/usr/bin/env python3
"""Export reviewed markdown reports to Word docx files."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "final"
SEARCH_DIRS = [
    ROOT,
    ROOT / "outputs" / "drafts",
    ROOT / "outputs" / "final",
    ROOT / "data" / "past_markdown_files",
]


def require_suffix(path: Path, suffix: str, role: str) -> None:
    if path.suffix.lower() != suffix:
        raise SystemExit(f"{role} must be a `{suffix}` file: {path}")


def ensure_output_available(output_path: Path, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        raise SystemExit(f"Output already exists: {output_path}. Use --overwrite to replace it.")


def require_pandoc() -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("pandoc is required. Install pandoc before exporting markdown to docx.")
    return pandoc


def resolve_markdown_path(raw_source: str) -> Path:
    candidate = Path(raw_source)
    if candidate.is_absolute() and candidate.exists():
        require_suffix(candidate, ".md", "Source")
        return candidate

    for base_dir in SEARCH_DIRS:
        path = base_dir / raw_source
        if path.exists():
            require_suffix(path, ".md", "Source")
            return path

    raise SystemExit(f"Markdown source not found: {raw_source}")


def default_output_path(source_path: Path) -> Path:
    return DEFAULT_OUTPUT_DIR / f"{source_path.stem}.docx"


def resolve_reference_doc(raw_reference_doc: Path | None) -> Path | None:
    if raw_reference_doc is None:
        return None
    if not raw_reference_doc.exists():
        raise SystemExit(f"Reference docx not found: {raw_reference_doc}")
    require_suffix(raw_reference_doc, ".docx", "Reference doc")
    return raw_reference_doc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Reviewed markdown file, typically in outputs/drafts/.")
    parser.add_argument("--output", type=Path, help="Output .docx path. Defaults to outputs/final/.")
    parser.add_argument("--reference-doc", type=Path, help="Optional pandoc reference .docx for Word styles.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    pandoc = require_pandoc()
    source_path = resolve_markdown_path(args.source)
    output_path = args.output or default_output_path(source_path)
    reference_doc = resolve_reference_doc(args.reference_doc)

    require_suffix(output_path, ".docx", "Output")
    ensure_output_available(output_path, args.overwrite)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        pandoc,
        str(source_path),
        "--from",
        "gfm",
        "--to",
        "docx",
        "--output",
        str(output_path),
    ]
    if reference_doc:
        command.extend(["--reference-doc", str(reference_doc)])

    subprocess.run(command, cwd=ROOT, check=True)
    print(f"Wrote Word document to {output_path}")


if __name__ == "__main__":
    main()
