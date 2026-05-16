#!/usr/bin/env python3
"""Translate a Japanese markdown report into English using retrieved examples and the OpenAI Responses API."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data" / "past_markdown_files"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "drafts"
DEFAULT_PROMPT = PROJECT_ROOT / "prompt.md"
DEFAULT_MEMORY = PROJECT_ROOT / "data" / "knowledge" / "section_pairs.jsonl"
DEFAULT_KNOWLEDGE = PROJECT_ROOT / "data" / "knowledge"
DEFAULT_API_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/responses"
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.2")
CA_BUNDLE_CANDIDATES = [
    "/etc/ssl/cert.pem",
    "/opt/homebrew/etc/openssl@3/cert.pem",
    "/opt/homebrew/etc/openssl/cert.pem",
    "/usr/local/etc/openssl@3/cert.pem",
    "/usr/local/etc/openssl/cert.pem",
]


def load_prepare_module(script_path: Path):
    spec = importlib.util.spec_from_file_location("prepare_translation_prompt", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_source_path(raw_source: str) -> Path:
    candidate = Path(raw_source)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    direct = PROJECT_ROOT / raw_source
    if direct.exists():
        return direct

    corpus_candidate = DEFAULT_SOURCE_DIR / raw_source
    if corpus_candidate.exists():
        return corpus_candidate

    raise SystemExit(f"Source markdown not found: {raw_source}")


def default_output_path(source_path: Path) -> Path:
    if "_J_" in source_path.name:
        return DEFAULT_OUTPUT_DIR / source_path.name.replace("_J_", "_E_", 1)
    return DEFAULT_OUTPUT_DIR / f"{source_path.stem}.en.md"


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\u3040-\u30ff\u3400-\u9fff-]+", "-", text.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "section"


def build_prompt(prepare, sections, index, section, template_text, memory_records, knowledge_docs, top_k, knowledge_top_k):
    query_labels = prepare.infer_section_labels(str(section["heading"]), str(section["body"]))

    scored_examples = [
        (
            prepare.score_texts(
                str(section["heading"]),
                str(section["body"]),
                str(record["jp_heading"]),
                str(record["jp_text"]),
            ),
            record,
        )
        for record in memory_records
    ]
    scored_examples = [item for item in scored_examples if item[0] > 0]
    scored_examples.sort(key=lambda item: item[0], reverse=True)

    scored_knowledge = [
        (
            prepare.score_texts(
                str(section["heading"]),
                str(section["body"]),
                str(doc["title"]),
                str(doc["text"]),
            )
            + prepare.knowledge_bonus(query_labels, doc),
            doc,
        )
        for doc in knowledge_docs
    ]
    scored_knowledge = [item for item in scored_knowledge if item[0] > 0]
    scored_knowledge.sort(key=lambda item: item[0], reverse=True)

    return (
        template_text.replace("{context}", prepare.build_context(sections, index))
        .replace("{knowledge_snippets}", prepare.format_knowledge(scored_knowledge, knowledge_top_k))
        .replace("{similar_sentences}", prepare.format_examples(scored_examples, top_k))
        .replace("{japanese_text}", prepare.render_section(section))
    )


def extract_output_text(payload: dict) -> str:
    texts: list[str] = []

    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                texts.append(content["text"])

    if texts:
        return "".join(texts).strip()

    error = payload.get("error")
    if error:
        raise RuntimeError(error.get("message", "Unknown API error"))

    raise RuntimeError("No output_text found in response payload.")


def clean_model_output(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    cleaned = re.sub(r"^(Here is the translation:|English Translation:)\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def build_ssl_context() -> ssl.SSLContext:
    configured_paths = [
        os.environ.get("SSL_CERT_FILE"),
        os.environ.get("REQUESTS_CA_BUNDLE"),
        *CA_BUNDLE_CANDIDATES,
    ]
    for raw_path in configured_paths:
        if raw_path and Path(raw_path).exists():
            return ssl.create_default_context(cafile=raw_path)
    return ssl.create_default_context()


def call_openai(api_key: str, model: str, prompt: str, instructions: str, reasoning_effort: str, timeout: int) -> str:
    body = {
        "model": model,
        "instructions": instructions,
        "input": prompt,
    }

    if reasoning_effort:
        body["reasoning"] = {"effort": reasoning_effort}

    request = urllib.request.Request(
        DEFAULT_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout, context=build_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API HTTP {exc.code}: {details}") from exc

    return clean_model_output(extract_output_text(payload))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source Japanese markdown filename or path. Files are typically placed in data/past_markdown_files.")
    parser.add_argument("--output", type=Path, help="Output path. Defaults to outputs/drafts/.")
    parser.add_argument("--section", action="append", dest="sections", help="Translate only specific heading(s). Repeatable.")
    parser.add_argument("--max-sections", type=int, help="Limit the number of sections translated, in source order.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--knowledge-top-k", type=int, default=2)
    parser.add_argument("--prompt-dir", type=Path, help="Optional directory to write assembled section prompts for debugging.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required.")

    source_path = resolve_source_path(args.source)
    output_path = args.output or default_output_path(source_path)
    if output_path.exists() and not args.overwrite:
        raise SystemExit(f"Output already exists: {output_path}. Use --overwrite to replace it.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prepare_script = PROJECT_ROOT / "skills" / "report-translation-workflow" / "scripts" / "prepare_translation_prompt.py"
    prepare = load_prepare_module(prepare_script)

    sections = prepare.parse_sections(source_path.read_text(encoding="utf-8"))
    template_text = DEFAULT_PROMPT.read_text(encoding="utf-8")
    memory_records = prepare.load_records(DEFAULT_MEMORY)
    knowledge_docs = prepare.load_knowledge_docs(DEFAULT_KNOWLEDGE)

    selected: list[tuple[int, dict[str, object]]] = []
    if args.sections:
        for heading in args.sections:
            index, section = prepare.find_section(sections, heading)
            selected.append((index, section))
    else:
        selected = list(enumerate(sections))

    if args.max_sections is not None:
        selected = selected[: args.max_sections]

    if args.prompt_dir:
        args.prompt_dir.mkdir(parents=True, exist_ok=True)

    instructions = (
        "Translate the current Japanese markdown section into natural, investor-facing English markdown. "
        "Return only the translated markdown section. Preserve heading depth, lists, block quotes, tables, and emphasis. "
        "Translate the heading itself. Keep names, dates, numbers, and fund names faithful to the source. "
        "Do not add commentary, code fences, or explanatory notes."
    )

    translated_sections: list[str] = []
    for position, (index, section) in enumerate(selected, start=1):
        heading = str(section["heading"]) or f"section-{position}"
        print(f"[{position}/{len(selected)}] Translating: {heading}", file=sys.stderr)

        prompt = build_prompt(
            prepare=prepare,
            sections=sections,
            index=index,
            section=section,
            template_text=template_text,
            memory_records=memory_records,
            knowledge_docs=knowledge_docs,
            top_k=args.top_k,
            knowledge_top_k=args.knowledge_top_k,
        )

        if args.prompt_dir:
            prompt_path = args.prompt_dir / f"{position:03d}_{slugify(heading)}.prompt.md"
            prompt_path.write_text(prompt, encoding="utf-8")

        translated = call_openai(
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            instructions=instructions,
            reasoning_effort=args.reasoning_effort,
            timeout=args.timeout,
        )
        translated_sections.append(translated)
        time.sleep(0.2)

    output_path.write_text("\n\n".join(section.strip() for section in translated_sections).strip() + "\n", encoding="utf-8")
    print(f"Wrote translation draft to {output_path}")


if __name__ == "__main__":
    main()
