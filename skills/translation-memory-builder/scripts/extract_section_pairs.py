#!/usr/bin/env python3
"""Build a section-level bilingual memory file from past markdown reports."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
IMAGE_RE = re.compile(r"!\[.*?\]\(.*?\)|<img[^>]*>", re.IGNORECASE)
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
    cleaned = IMAGE_RE.sub("", cleaned)
    cleaned = re.sub(r"\\?\[(図中|キャプチャ|ページ下部に注記を加える)\\?\]", "", cleaned)
    cleaned = re.sub(r"<u>\\?\s*</u>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def parse_sections(text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        match = HEADING_RE.match(line)
        if match:
            if current is not None:
                current["body"] = "\n".join(current["body_lines"]).strip()
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
        current["body"] = "\n".join(current["body_lines"]).strip()
        del current["body_lines"]
        sections.append(current)

    return sections


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

    body = re.sub(r"\s+", "", body)
    return not body


def drop_noise_sections(sections: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        section
        for section in sections
        if not is_noise_body(str(section["body"]))
    ]


def infer_labels(heading: str, body: str) -> list[str]:
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
    if any(token in text for token in ["Credit", "クレジット", "Creditページ"]):
        labels.add("credit")
    if any(token in text for token in ["ケース", "Case Study", "Daytona", "Pyuru", "Kids Corporation", "ゆこゆこ", "デイトナ", "ピュール"]):
        labels.add("case-study")

    return sorted(labels)


def file_pairs(corpus_dir: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for jp_file in sorted(corpus_dir.glob("*_J_*.md")):
        en_name = jp_file.name.replace("_J_", "_E_", 1)
        en_file = corpus_dir / en_name
        if en_file.exists():
            pairs.append((jp_file, en_file))
    return pairs


def build_records(corpus_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    for jp_file, en_file in file_pairs(corpus_dir):
        jp_sections = drop_noise_sections(
            drop_preface_sections(
                parse_sections(jp_file.read_text(encoding="utf-8"))
            )
        )
        en_sections = drop_noise_sections(
            drop_preface_sections(
                parse_sections(en_file.read_text(encoding="utf-8"))
            )
        )
        common = min(len(jp_sections), len(en_sections))

        for idx in range(common):
            jp_section = jp_sections[idx]
            en_section = en_sections[idx]
            records.append(
                {
                    "jp_file": jp_file.name,
                    "en_file": en_file.name,
                    "section_index": idx,
                    "year": re.search(r"_(\d{4})\.md$", jp_file.name).group(1) if re.search(r"_(\d{4})\.md$", jp_file.name) else "",
                    "jp_heading": jp_section["heading"],
                    "en_heading": en_section["heading"],
                    "jp_level": jp_section["level"],
                    "en_level": en_section["level"],
                    "jp_text": clean_body(str(jp_section["body"])),
                    "en_text": clean_body(str(en_section["body"])),
                    "labels": infer_labels(str(jp_section["heading"]), clean_body(str(jp_section["body"]))),
                }
            )

    return records


def normalize_heading_key(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def build_heading_translation_records(
    section_records: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Create searchable heading-only records and place them before section memory."""
    grouped: dict[tuple[str, str], dict[str, object]] = {}

    for record in section_records:
        jp_heading = str(record.get("jp_heading", "")).strip()
        en_heading = str(record.get("en_heading", "")).strip()
        if not jp_heading or not en_heading:
            continue
        record_labels = record.get("labels", [])
        if not isinstance(record_labels, list):
            record_labels = []

        key = (normalize_heading_key(jp_heading), en_heading.lower())
        entry = grouped.setdefault(
            key,
            {
                "jp_heading": jp_heading,
                "en_heading": en_heading,
                "jp_level": record.get("jp_level", 1),
                "en_level": record.get("en_level", 1),
                "labels": set(["heading", *record_labels]),
                "occurrences": [],
                "years": set(),
            },
        )

        labels = entry["labels"]
        if isinstance(labels, set):
            labels.update(str(label) for label in record_labels)

        years = entry["years"]
        if isinstance(years, set) and record.get("year"):
            years.add(str(record["year"]))

        occurrences = entry["occurrences"]
        if isinstance(occurrences, list):
            occurrences.append(
                {
                    "jp_file": record.get("jp_file", ""),
                    "en_file": record.get("en_file", ""),
                    "section_index": record.get("section_index", ""),
                    "year": record.get("year", ""),
                }
            )

    heading_records: list[dict[str, object]] = []
    for idx, entry in enumerate(
        sorted(
            grouped.values(),
            key=lambda item: (
                str(item["jp_heading"]),
                str(item["en_heading"]).lower(),
            ),
        )
    ):
        labels = sorted(str(label) for label in entry["labels"]) if isinstance(entry["labels"], set) else ["heading"]
        years = sorted(str(year) for year in entry["years"]) if isinstance(entry["years"], set) else []
        occurrences = entry["occurrences"] if isinstance(entry["occurrences"], list) else []
        jp_heading = str(entry["jp_heading"])
        en_heading = str(entry["en_heading"])
        search_terms = sorted(
            {
                jp_heading,
                normalize_heading_key(jp_heading),
                en_heading,
                en_heading.lower(),
                *labels,
                *years,
            }
        )

        seen_in = ", ".join(
            f"{occurrence['jp_file']}#{occurrence['section_index']}->{occurrence['en_file']}"
            for occurrence in occurrences
        )
        heading_records.append(
            {
                "record_type": "heading_translation",
                "jp_file": "__heading_index__",
                "en_file": "__heading_index__",
                "section_index": idx,
                "year": ",".join(years),
                "jp_heading": jp_heading,
                "en_heading": en_heading,
                "jp_level": entry["jp_level"],
                "en_level": entry["en_level"],
                "jp_text": f"見出し翻訳対応: {jp_heading} -> {en_heading}\n出現: {seen_in}",
                "en_text": f"Heading translation: {jp_heading} -> {en_heading}",
                "labels": labels,
                "heading_search_terms": search_terms,
                "heading_occurrences": occurrences,
            }
        )

    return heading_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    section_records = build_records(args.corpus_dir)
    records = build_heading_translation_records(section_records) + section_records
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} translation memory records to {args.output}")


if __name__ == "__main__":
    main()
