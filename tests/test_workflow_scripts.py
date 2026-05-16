from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def load_module(relative_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


source_converter = load_module(
    "skills/report-source-preparation/scripts/convert_docx_to_markdown.py",
    "convert_docx_to_markdown",
)
docx_exporter = load_module(
    "skills/report-docx-export/scripts/export_markdown_to_docx.py",
    "export_markdown_to_docx",
)
translation_prompt = load_module(
    "skills/report-translation-workflow/scripts/prepare_translation_prompt.py",
    "prepare_translation_prompt",
)
memory_extractor = load_module(
    "skills/translation-memory-builder/scripts/extract_section_pairs.py",
    "extract_section_pairs",
)


class SourcePreparationScriptTests(unittest.TestCase):
    def test_resolve_docx_path_finds_raw_file_by_name(self) -> None:
        path = source_converter.resolve_docx_path("Unison Impact_J_2024.docx")
        self.assertEqual(path, source_converter.RAW_DIR / "Unison Impact_J_2024.docx")

    def test_resolve_docx_path_rejects_non_docx_absolute_file(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source = Path(tmp_dir) / "report.md"
            source.write_text("# Not docx\n", encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "Source must be a `.docx` file"):
                source_converter.resolve_docx_path(str(source))

    def test_docx_default_output_uses_markdown_corpus_dir(self) -> None:
        output = source_converter.default_output_path(Path("Unison Impact_J_2025.docx"))
        self.assertEqual(output, source_converter.MARKDOWN_DIR / "Unison Impact_J_2025.md")

    def test_docx_output_requires_markdown_suffix(self) -> None:
        with self.assertRaisesRegex(SystemExit, "Output must be a `.md` file"):
            source_converter.require_suffix(Path("bad.txt"), ".md", "Output")

    def test_docx_overwrite_guard(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "existing.md"
            output.write_text("exists", encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "Use --overwrite"):
                source_converter.ensure_output_available(output, overwrite=False)

            source_converter.ensure_output_available(output, overwrite=True)


class DocxExportScriptTests(unittest.TestCase):
    def test_resolve_markdown_path_finds_corpus_markdown_by_path(self) -> None:
        path = docx_exporter.resolve_markdown_path(
            "data/past_markdown_files/Unison Impact_E_2024.md"
        )
        self.assertEqual(
            path,
            docx_exporter.ROOT / "data" / "past_markdown_files" / "Unison Impact_E_2024.md",
        )

    def test_resolve_markdown_path_rejects_non_markdown_absolute_file(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source = Path(tmp_dir) / "report.docx"
            source.write_text("not markdown", encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "Source must be a `.md` file"):
                docx_exporter.resolve_markdown_path(str(source))

    def test_docx_export_default_output_uses_final_dir(self) -> None:
        output = docx_exporter.default_output_path(Path("Unison Impact_E_2025.md"))
        self.assertEqual(output, docx_exporter.DEFAULT_OUTPUT_DIR / "Unison Impact_E_2025.docx")

    def test_docx_export_output_requires_docx_suffix(self) -> None:
        with self.assertRaisesRegex(SystemExit, "Output must be a `.docx` file"):
            docx_exporter.require_suffix(Path("bad.md"), ".docx", "Output")

    def test_reference_doc_must_exist_and_be_docx(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            missing = Path(tmp_dir) / "missing.docx"
            wrong_suffix = Path(tmp_dir) / "reference.md"
            wrong_suffix.write_text("# Reference\n", encoding="utf-8")
            reference = Path(tmp_dir) / "reference.docx"
            reference.write_bytes(b"placeholder")

            with self.assertRaisesRegex(SystemExit, "Reference docx not found"):
                docx_exporter.resolve_reference_doc(missing)
            with self.assertRaisesRegex(SystemExit, "Reference doc must be a `.docx` file"):
                docx_exporter.resolve_reference_doc(wrong_suffix)
            self.assertEqual(docx_exporter.resolve_reference_doc(reference), reference)


class TranslationPromptScriptTests(unittest.TestCase):
    def test_heading_translation_records_are_searchable_first_class_memory(self) -> None:
        section_records = [
            {
                "jp_file": "Unison Impact_J_2024.md",
                "en_file": "Unison Impact_E_2024.md",
                "section_index": 1,
                "year": "2024",
                "jp_heading": "ユニゾンにおけるESGの取り組みとフレームワーク",
                "en_heading": "Unison’s Approach to ESG",
                "jp_level": 1,
                "en_level": 1,
                "jp_text": "ユニゾンは創業時から社会的価値を追求してきました。",
                "en_text": "Unison has strived to create social impact.",
                "labels": ["framework"],
            }
        ]

        heading_records = memory_extractor.build_heading_translation_records(section_records)
        self.assertEqual(heading_records[0]["record_type"], "heading_translation")
        self.assertEqual(
            heading_records[0]["jp_heading"],
            "ユニゾンにおけるESGの取り組みとフレームワーク",
        )
        self.assertIn("heading_search_terms", heading_records[0])

        records = heading_records + section_records
        memory_index = translation_prompt.build_memory_index(records)
        candidates = translation_prompt.retrieve_memory_candidates(
            memory_index,
            "ユニゾンにおけるESGの取り組みとフレームワーク",
            "見出しの訳語を確認します。",
            {"framework"},
            candidate_limit=1,
        )

        self.assertEqual(candidates, [heading_records[0]])

    def test_memory_index_retrieves_related_section_pairs(self) -> None:
        records = [
            {
                "jp_heading": "ごあいさつ",
                "jp_text": "投資家の皆さま\n今年もレポートをお届けします。",
                "en_heading": "Greeting",
                "en_text": "To our valued investors,",
                "labels": ["greeting"],
            },
            {
                "jp_heading": "編集後記",
                "jp_text": "編集長からのコメントです。",
                "en_heading": "Afterword",
                "en_text": "Afterword",
                "labels": ["afterword"],
            },
        ]

        memory_index = translation_prompt.build_memory_index(records)
        candidates = translation_prompt.retrieve_memory_candidates(
            memory_index,
            "ごあいさつ",
            "投資家の皆さま\n今年もユニゾンのレポートをお届けします。",
            {"greeting"},
            candidate_limit=1,
        )

        self.assertEqual(candidates, [records[0]])


if __name__ == "__main__":
    unittest.main()
