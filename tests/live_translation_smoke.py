#!/usr/bin/env python3
"""Live OpenAI smoke test for the translation runner."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required for live translation smoke tests.", file=sys.stderr)
        return 1

    model = os.environ.get("OPENAI_SMOKE_MODEL", os.environ.get("OPENAI_MODEL", "gpt-5.2"))

    with TemporaryDirectory(prefix="uc-live-translation-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        source = tmp_path / "smoke_J_2099.md"
        output = tmp_path / "smoke_E_2099.md"
        prompt_dir = tmp_path / "prompts"

        source.write_text(
            "# ごあいさつ\n\n"
            "本テストは翻訳ランナーの疎通確認です。数値 123 と Unison Capital は変更しないでください。\n",
            encoding="utf-8",
        )

        command = [
            sys.executable,
            "src/translate_report.py",
            str(source),
            "--output",
            str(output),
            "--prompt-dir",
            str(prompt_dir),
            "--max-sections",
            "1",
            "--model",
            model,
            "--reasoning-effort",
            "low",
            "--timeout",
            "240",
            "--overwrite",
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            print(result.stdout, file=sys.stdout)
            print(result.stderr, file=sys.stderr)
            return result.returncode

        if not output.exists():
            print(f"Expected translation output was not created: {output}", file=sys.stderr)
            return 1

        translated = output.read_text(encoding="utf-8").strip()
        if not translated:
            print("Translation output is empty.", file=sys.stderr)
            return 1
        if "```" in translated:
            print("Translation output must not contain code fences.", file=sys.stderr)
            return 1
        if not any(prompt_dir.glob("*.prompt.md")):
            print("Expected debug prompt was not written.", file=sys.stderr)
            return 1

    print("Live translation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
