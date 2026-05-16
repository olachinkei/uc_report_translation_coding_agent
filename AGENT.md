# AGENT.md

AI Agent / 開発者向けの短い作業メモです。ビジネスユーザー向けの説明は [README.md](README.md)、詳しい設計と運用は [docs/index.md](docs/index.md) を参照してください。

## 目的

この repository は、ユニゾンの日本語レポートを英語 markdown に翻訳し、必要に応じて Word `.docx` へ戻すための作業場所です。

翻訳は Codex に依頼して進める前提です。OpenAI API key は使いません。

## 使う Skill

- `$report-source-preparation`: Word `.docx` や粗い markdown を、翻訳しやすい日本語 markdown に整える
- `$translation-memory-builder`: 過去の日英 markdown から section pair と reusable knowledge を整備する
- `$report-translation-workflow`: 過去例、`prompt.md`、`data/knowledge` を参照して英語 markdown を作成・修正する
- `$report-docx-export`: レビュー済み markdown を Word `.docx` に変換する

## 作業ルール

- 原本 `.docx` は編集しない
- corpus を直すときは markdown 側だけを整える
- 数値、年号、固有名詞、ファンド名は変えない
- recurring な翻訳判断は `prompt.md` または `data/knowledge` に残す
- 単発の case study 詳細は `data/knowledge` に入れすぎない
- 出力途中の翻訳は `outputs/drafts`、納品候補は `outputs/final` に置く

## メンテナンス

過去レポートや heading を更新したら、alignment を確認してから memory を再生成します。

```bash
python3 skills/translation-memory-builder/scripts/validate_corpus_alignment.py \
  --corpus-dir data/past_markdown_files \
  --strict
```

```bash
python3 skills/translation-memory-builder/scripts/extract_section_pairs.py \
  --corpus-dir data/past_markdown_files \
  --output data/knowledge/section_pairs.jsonl
```

## 完了前チェック

```bash
make check
```

`make check` は OpenAI API key なしで通る必要があります。
