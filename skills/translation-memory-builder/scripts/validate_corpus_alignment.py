#!/usr/bin/env python3
"""Report JP/EN markdown section alignment gaps in the past corpus."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def load_extract_module(script_path: Path):
    spec = importlib.util.spec_from_file_location("extract_section_pairs", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path)
    parser.add_argument("--jp-file", type=Path)
    parser.add_argument("--en-file", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    script_path = Path(__file__).resolve().parent / "extract_section_pairs.py"
    extractor = load_extract_module(script_path)

    if args.jp_file or args.en_file:
        if not args.jp_file or not args.en_file:
            raise SystemExit("Both --jp-file and --en-file are required when validating a specific pair.")
        file_pairs = [(args.jp_file, args.en_file)]
    elif args.corpus_dir:
        file_pairs = extractor.file_pairs(args.corpus_dir)
    else:
        raise SystemExit("Specify either --jp-file/--en-file or --corpus-dir.")

    had_gap = False
    for jp_file, en_file in file_pairs:
        extractor.require_markdown(jp_file, "Japanese source")
        extractor.require_markdown(en_file, "English source")
        jp_sections = extractor.drop_noise_sections(
            extractor.drop_preface_sections(
                extractor.parse_sections(jp_file.read_text(encoding="utf-8"))
            )
        )
        en_sections = extractor.drop_noise_sections(
            extractor.drop_preface_sections(
                extractor.parse_sections(en_file.read_text(encoding="utf-8"))
            )
        )

        print(f"\n[{jp_file.name} -> {en_file.name}]")
        print(f"JP sections: {len(jp_sections)} | EN sections: {len(en_sections)}")

        common = min(len(jp_sections), len(en_sections))
        for idx in range(common):
            jp_heading = str(jp_sections[idx]["heading"])
            en_heading = str(en_sections[idx]["heading"])
            print(f"{idx:02d}. JP={jp_heading!r} | EN={en_heading!r}")

        if len(jp_sections) != len(en_sections):
            had_gap = True
            print("Count mismatch detected.")
            if len(jp_sections) > len(en_sections):
                extras = [str(section["heading"]) for section in jp_sections[len(en_sections) :]]
                print(f"Extra JP sections: {extras}")
            else:
                extras = [str(section["heading"]) for section in en_sections[len(jp_sections) :]]
                print(f"Extra EN sections: {extras}")

    if args.strict and had_gap:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
