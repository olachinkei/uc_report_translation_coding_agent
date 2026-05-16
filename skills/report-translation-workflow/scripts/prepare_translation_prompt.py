#!/usr/bin/env python3
"""Assemble a section-focused translation prompt with retrieved bilingual examples."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import re
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
WORD_RE = re.compile(r"[A-Za-z0-9]+|[\u3040-\u30ff\u3400-\u9fff]{2,}")
BODY_NOISE_LINE_PATTERNS = [
    re.compile(r"^コンテンツ・タイトル$"),
    re.compile(r"^前段説明書き$"),
    re.compile(r"^前文説明書き$"),
    re.compile(r"^対談相手紹介$"),
    re.compile(r"^対談本文"),
    re.compile(r"^資さん基本情報文（欄外小文字）$"),
    re.compile(r"^＜欄外小文字＞$"),
    re.compile(r"^【別欄での表示】$"),
    re.compile(r"^[x×]$", re.IGNORECASE),
    re.compile(r"^キャプチャ[0-9①-⑳]+[:：].*$"),
    re.compile(r"^（挿入図[:：].*）$"),
    re.compile(r"^\*\*（以下、本文）\*\*$"),
]
BODY_PREFIX_PATTERNS = [
    re.compile(r"^(前文説明書き|前段説明書き)[:：]\s*"),
    re.compile(r"^Foreword:\s*", re.IGNORECASE),
]


def clean_body(text: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        normalized = raw_line.rstrip()
        for pattern in BODY_PREFIX_PATTERNS:
            normalized = pattern.sub("", normalized)

        stripped = normalized.strip()
        if any(pattern.match(stripped) for pattern in BODY_NOISE_LINE_PATTERNS):
            continue
        cleaned_lines.append(normalized)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def looks_like_preface(section: dict[str, object]) -> bool:
    if section["heading"]:
        return False

    body = str(section["body"]).strip()
    if not body:
        return True

    lowered = body.lower()
    if "contents" in lowered or "目次" in body:
        return True

    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines:
        return True

    short_lines = sum(1 for line in lines if len(line) <= 40)
    if len(lines) >= 4 and short_lines / len(lines) >= 0.7:
        return True

    return False


def drop_preface_sections(sections: list[dict[str, object]]) -> list[dict[str, object]]:
    trimmed = list(sections)
    while trimmed and looks_like_preface(trimmed[0]):
        trimmed.pop(0)
    return trimmed


def is_noise_body(text: str) -> bool:
    body = clean_body(text)
    if not body:
        return True

    compact = re.sub(r"\s+", "", body)
    return not compact


def drop_noise_sections(sections: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        section
        for section in sections
        if not is_noise_body(str(section["body"]))
    ]


def parse_sections(text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        match = HEADING_RE.match(line)
        if match:
            if current is not None:
                current["body"] = clean_body("\n".join(current["body_lines"]))
                del current["body_lines"]
                sections.append(current)
            current = {
                "level": len(match.group(1)),
                "heading": match.group(2).strip(),
                "body_lines": [],
            }
            continue

        if current is None:
            if line.strip():
                current = {"level": 0, "heading": "", "body_lines": [line]}
            continue

        current["body_lines"].append(line)

    if current is not None:
        current["body"] = clean_body("\n".join(current["body_lines"]))
        del current["body_lines"]
        sections.append(current)

    return sections


def tokenize(text: str) -> set[str]:
    tokens = {token.lower() for token in WORD_RE.findall(text)}
    compact = re.sub(r"\s+", "", text)
    for size in (2, 3):
        for idx in range(max(0, len(compact) - size + 1)):
            chunk = compact[idx : idx + size]
            if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", chunk):
                tokens.add(chunk)
    return tokens


def score_texts(
    query_heading: str,
    query_body: str,
    candidate_heading: str,
    candidate_body: str,
) -> float:
    query_tokens = tokenize(f"{query_heading}\n{query_body}")
    candidate_tokens = tokenize(f"{candidate_heading}\n{candidate_body}")
    if not query_tokens or not candidate_tokens:
        return 0.0

    overlap = len(query_tokens & candidate_tokens)
    union = len(query_tokens | candidate_tokens)
    base = overlap / union if union else 0.0

    heading_bonus = 0.0
    if query_heading and candidate_heading:
        if query_heading == candidate_heading:
            heading_bonus = 0.4
        elif query_heading in candidate_heading or candidate_heading in query_heading:
            heading_bonus = 0.2

    return base + heading_bonus


def infer_section_labels(heading: str, body: str) -> set[str]:
    text = f"{heading}\n{body}"
    lowered = text.lower()
    labels: set[str] = set()

    if "ごあいさつ" in text or "to our valued investors" in lowered:
        labels.add("greeting")
    if "編集後記" in text or "afterword" in lowered:
        labels.add("afterword")
    if any(token in text for token in ["可視化", "定量化", "RIMM", "EDCI"]):
        labels.add("quantification")
    if "visualization" in lowered or "quantification" in lowered:
        labels.add("quantification")
    if "フレームワーク" in text or "guiding principles" in lowered or "approach to esg" in lowered:
        labels.add("framework")
    if any(token in text for token in ["CDE", "第一段階", "第二段階", "Community, Diversity", "Carbon, Disposables"]):
        labels.add("cde")

    return labels


def knowledge_bonus(query_labels: set[str], doc: dict[str, str]) -> float:
    if not query_labels:
        return 0.0

    haystack = f"{doc['name']} {doc['title']}".lower()
    bonus = 0.0

    if "greeting" in query_labels and "greeting" in haystack:
        bonus += 0.6
    if "afterword" in query_labels and "afterword" in haystack:
        bonus += 0.6
    if "quantification" in query_labels and any(
        token in haystack for token in ["visualization", "quantification", "rimm", "edci"]
    ):
        bonus += 0.45
    if "framework" in query_labels and any(
        token in haystack for token in ["ucesg", "approach to esg", "framework", "esg"]
    ):
        bonus += 0.35
    if "cde" in query_labels and any(
        token in haystack for token in ["cde", "two stage"]
    ):
        bonus += 0.45

    return bonus


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def find_section(sections: list[dict[str, object]], heading: str) -> tuple[int, dict[str, object]]:
    for idx, section in enumerate(sections):
        if str(section["heading"]) == heading:
            return idx, section

    normalized = normalize_heading(heading)
    normalized_matches = [
        (idx, section)
        for idx, section in enumerate(sections)
        if normalize_heading(str(section["heading"])) == normalized
    ]
    if len(normalized_matches) == 1:
        return normalized_matches[0]

    fuzzy_matches = [
        (idx, section)
        for idx, section in enumerate(sections)
        if normalized and normalized in normalize_heading(str(section["heading"]))
    ]
    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0]

    available = ", ".join(str(section["heading"]) for section in sections if section["heading"])
    raise SystemExit(f'Section "{heading}" not found. Available headings: {available}')


def load_records(memory_file: Path) -> list[dict[str, object]]:
    with memory_file.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def record_labels(record: dict[str, object]) -> set[str]:
    labels = record.get("labels", [])
    if isinstance(labels, list):
        return {str(label) for label in labels}
    return set()


def build_memory_index(records: list[dict[str, object]]) -> dict[str, object]:
    """Build a tiny inverted index so prompt retrieval does not scan into context."""
    inverted: dict[str, set[int]] = defaultdict(set)
    tokens_by_record: list[set[str]] = []
    labels_by_record: list[set[str]] = []
    normalized_headings: list[str] = []
    record_types: list[str] = []

    for idx, record in enumerate(records):
        labels = record_labels(record)
        heading_search_terms = record.get("heading_search_terms", [])
        if not isinstance(heading_search_terms, list):
            heading_search_terms = []
        labels_by_record.append(labels)
        normalized_headings.append(normalize_heading(str(record.get("jp_heading", ""))))
        record_types.append(str(record.get("record_type", "section_pair")))

        searchable_text = "\n".join(
            [
                str(record.get("record_type", "")),
                str(record.get("jp_heading", "")),
                str(record.get("jp_text", "")),
                str(record.get("en_heading", "")),
                str(record.get("en_text", "")),
                " ".join(str(term) for term in heading_search_terms),
                " ".join(labels),
            ]
        )
        tokens = tokenize(searchable_text)
        tokens_by_record.append(tokens)
        for token in tokens:
            inverted[token].add(idx)

    return {
        "inverted": dict(inverted),
        "labels_by_record": labels_by_record,
        "normalized_headings": normalized_headings,
        "record_types": record_types,
        "records": records,
        "tokens_by_record": tokens_by_record,
    }


def retrieve_memory_candidates(
    memory_index: dict[str, object],
    query_heading: str,
    query_body: str,
    query_labels: set[str],
    candidate_limit: int,
) -> list[dict[str, object]]:
    records = memory_index["records"]
    inverted = memory_index["inverted"]
    labels_by_record = memory_index["labels_by_record"]
    normalized_headings = memory_index["normalized_headings"]
    record_types = memory_index.get("record_types", [])

    if not isinstance(records, list):
        return []

    query_tokens = tokenize(f"{query_heading}\n{query_body}")
    candidate_scores: Counter[int] = Counter()
    for token in query_tokens:
        for record_idx in inverted.get(token, set()):
            candidate_scores[int(record_idx)] += 1

    normalized_query_heading = normalize_heading(query_heading)
    for idx, heading in enumerate(normalized_headings):
        if normalized_query_heading and (
            heading == normalized_query_heading
            or normalized_query_heading in heading
            or heading in normalized_query_heading
        ):
            candidate_scores[idx] += 40
            if isinstance(record_types, list) and idx < len(record_types) and record_types[idx] == "heading_translation":
                candidate_scores[idx] += 500

    if query_labels:
        for idx, labels in enumerate(labels_by_record):
            overlap = len(query_labels & labels)
            if overlap:
                candidate_scores[idx] += 12 * overlap

    if not candidate_scores:
        return records[:candidate_limit]

    selected = [
        records[idx]
        for idx, _score in candidate_scores.most_common(max(candidate_limit, 1))
    ]
    return selected


def clip(text: str, limit: int = 900) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def build_context(sections: list[dict[str, object]], index: int) -> str:
    parts: list[str] = []
    if index > 0:
        prev = sections[index - 1]
        parts.append(
            "Previous section:\n"
            f"Heading: {prev['heading']}\n"
            f"{clip(str(prev['body']), 500)}"
        )
    current = sections[index]
    parts.append(f"Current heading: {current['heading']}")
    if index + 1 < len(sections):
        nxt = sections[index + 1]
        parts.append(
            "Next section:\n"
            f"Heading: {nxt['heading']}\n"
            f"{clip(str(nxt['body']), 500)}"
        )
    return "\n\n".join(parts)


def load_knowledge_docs(knowledge_dir: Path | None) -> list[dict[str, str]]:
    if knowledge_dir is None or not knowledge_dir.exists():
        return []

    docs: list[dict[str, str]] = []
    for path in sorted(knowledge_dir.glob("*.txt")):
        raw_title = re.sub(r"^[0-9]+[_-]*", "", path.stem).replace("_", " ").strip()
        text = path.read_text(encoding="utf-8")
        sections = parse_sections(text)

        section_docs = [
            section
            for section in sections
            if str(section["heading"]).strip() and str(section["body"]).strip()
        ]

        if not section_docs:
            docs.append(
                {
                    "name": path.name,
                    "title": raw_title or path.stem,
                    "text": text,
                }
            )
            continue

        for section in section_docs:
            docs.append(
                {
                    "name": path.name,
                    "title": f"{raw_title} / {section['heading']}".strip(" /"),
                    "text": str(section["body"]),
                }
            )
    return docs


def render_section(section: dict[str, object]) -> str:
    heading = str(section["heading"]).strip()
    body = str(section["body"]).strip()
    level = int(section["level"])

    if heading and level > 0:
        heading_line = f"{'#' * level} {heading}"
        return f"{heading_line}\n\n{body}".strip()
    return body


def format_examples(records: list[tuple[float, dict[str, object]]], top_k: int) -> str:
    if not records:
        return "No close bilingual examples found."

    blocks: list[str] = []
    for rank, (value, record) in enumerate(records[:top_k], start=1):
        if record.get("record_type") == "heading_translation":
            occurrences = record.get("heading_occurrences", [])
            seen_in = ""
            if isinstance(occurrences, list):
                seen_in = ", ".join(
                    f"{occurrence.get('jp_file', '')}#{occurrence.get('section_index', '')}"
                    for occurrence in occurrences[:5]
                    if isinstance(occurrence, dict)
                )
            blocks.append(
                "\n".join(
                    [
                        f"### Example {rank} | score={value:.3f} | heading mapping",
                        f"JP heading: {record['jp_heading']}",
                        f"EN heading: {record['en_heading']}",
                        f"Seen in: {seen_in or record.get('year', '')}",
                    ]
                )
            )
            continue
        blocks.append(
            "\n".join(
                [
                    f"### Example {rank} | score={value:.3f}",
                    f"Source: {record['jp_file']} -> {record['en_file']}",
                    f"JP heading: {record['jp_heading']}",
                    f"EN heading: {record['en_heading']}",
                    "JP:",
                    clip(str(record["jp_text"])),
                    "EN:",
                    clip(str(record["en_text"])),
                ]
            )
        )
    return "\n\n".join(blocks)


def format_knowledge(docs: list[tuple[float, dict[str, str]]], top_k: int) -> str:
    if not docs:
        return "No curated knowledge snippet selected."

    blocks: list[str] = []
    for rank, (value, doc) in enumerate(docs[:top_k], start=1):
        blocks.append(
            "\n".join(
                [
                    f"### Knowledge {rank} | score={value:.3f}",
                    f"Source: {doc['name']}",
                    f"Title: {doc['title']}",
                    clip(doc["text"], 1200),
                ]
            )
        )
    return "\n\n".join(blocks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-md", required=True, type=Path)
    parser.add_argument("--section", required=True)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--memory-file", required=True, type=Path)
    parser.add_argument("--knowledge-dir", type=Path)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--candidate-limit", type=int, default=25)
    parser.add_argument("--knowledge-top-k", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    sections = drop_noise_sections(
        drop_preface_sections(
            parse_sections(args.source_md.read_text(encoding="utf-8"))
        )
    )
    index, section = find_section(sections, args.section)
    records = load_records(args.memory_file)
    memory_index = build_memory_index(records)
    knowledge_docs = load_knowledge_docs(args.knowledge_dir)
    query_labels = infer_section_labels(args.section, str(section["body"]))
    candidate_records = retrieve_memory_candidates(
        memory_index,
        args.section,
        str(section["body"]),
        query_labels,
        args.candidate_limit,
    )

    scored = [
        (
            score_texts(
                args.section,
                str(section["body"]),
                str(record["jp_heading"]),
                str(record["jp_text"]),
            )
            + (
                1.0
                if record.get("record_type") == "heading_translation"
                and normalize_heading(args.section) == normalize_heading(str(record.get("jp_heading", "")))
                else 0.0
            ),
            record,
        )
        for record in candidate_records
    ]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: item[0], reverse=True)

    scored_knowledge = [
        (
            score_texts(
                args.section,
                str(section["body"]),
                str(doc["title"]),
                str(doc["text"]),
            )
            + knowledge_bonus(query_labels, doc),
            doc,
        )
        for doc in knowledge_docs
    ]
    scored_knowledge = [item for item in scored_knowledge if item[0] > 0]
    scored_knowledge.sort(key=lambda item: item[0], reverse=True)

    template = args.template.read_text(encoding="utf-8")
    output = (
        template.replace("{context}", build_context(sections, index))
        .replace("{knowledge_snippets}", format_knowledge(scored_knowledge, args.knowledge_top_k))
        .replace("{similar_sentences}", format_examples(scored, args.top_k))
        .replace("{japanese_text}", render_section(section))
    )

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote prompt to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
