# UC Report Translation Coding Agent

この repository は、ユニゾンの日本語レポートを英語レポートへ翻訳し、必要に応じて Word `.docx` まで戻すための作業場所です。

ビジネスユーザーは、基本的に **Codex に依頼するだけ** で作業を進めます。コマンド実行、ファイル変換、翻訳、レビュー、出力作成は Codex が行います。

## この Repository の役割

- 新しい日本語 `.docx` を翻訳しやすい markdown `.md` に変換する
- 日本語 markdown を英語 markdown に翻訳する
- 翻訳済み markdown をレビュー・修正する
- レビュー済み markdown を Word `.docx` に変換する
- 過去レポートを translation memory として蓄積する

## 利用できる Skills と使い方

この repository には、Codex が作業内容に応じて使う専用 skill が 4つあります。ユーザーが細かいコマンドを覚える必要はありませんが、依頼文に skill 名を含めると、Codex がより迷わず作業できます。

| 用途 | skill | 主な入出力 | Codex への依頼例 |
| --- | --- | --- | --- |
| 既存の Word 原稿や markdown 原稿から、翻訳準備用の日本語 markdown を作る | `@report-source-preparation` | `data/past_raw_files/*.docx` / `*.md` → `data/past_markdown_files/*_J_*.md` | `@report-source-preparation` を使って、`data/past_raw_files/Unison Impact_J_2025.docx` を md file に変更してください。 |
| 日本語 markdown を英語 markdown に翻訳し、過去訳・辞書・見出し対応表を参照してレビューする | `@report-translation-workflow` | `data/past_markdown_files/*_J_*.md` → `outputs/drafts/*_E_*.md` | `@report-translation-workflow` を使って、`data/past_markdown_files/Unison Impact_J_2025.md` を英語に翻訳して。 |
| 指定した日英 markdown ペアから、再利用できる翻訳メモリと見出し対応表を更新する | `@translation-memory-builder` | `data/past_markdown_files/*_J_*.md` + `*_E_*.md` → `data/knowledge/section_pairs.jsonl` | `@translation-memory-builder` を使って、`data/past_markdown_files/Unison Impact_J_2025.md` と `data/past_markdown_files/Unison Impact_E_2025.md` から `data/knowledge/section_pairs.jsonl` を更新してください。 |
| レビュー済み markdown から Word `.docx` を作成する | `@report-docx-export` | `outputs/drafts/*.md` → `outputs/final/*.docx` | `@report-docx-export` を使って、`outputs/drafts/Unison Impact_E_2025.md` を Wordファイルに変換して。 |

レビューや修正も、同じ `@report-translation-workflow` に依頼できます。

```text
@report-translation-workflow を使って、
outputs/drafts/Unison Impact_E_2025.md を、
data/past_markdown_files/Unison Impact_J_2025.md と照合してレビューしてください。

数値、固有名詞、見出し構造、抜け漏れを重点的に見てください。
```

大きな修正が複数ある場合は、対象 section と変更方針を分けて Codex に依頼すると安定します。

```text
@report-translation-workflow を使って、
outputs/drafts/Unison Impact_E_2025.md を修正してください。

1. 「Greeting」の第 3 段落を、投資家向けに少し自然で前向きな表現にしてください。
2. 「Visualization of Impact through Quantification」は 2024 年版の言い回しに寄せてください。
3. Company description は事実を変えず、少し簡潔にしてください。
4. 数値、年号、会社名、ファンド名は変更しないでください。
```

Word の見た目を既存テンプレートに寄せたい場合は、reference docx も一緒に指定してください。

```text
@report-docx-export を使って、
outputs/drafts/Unison Impact_E_2025.md を Word docx に変換してください。
path/to/reference.docx を reference docx として使ってください。
```

## その他

来年の翻訳のために、最終化されたファイルを保存する場所、翻訳プロンプト・辞書の場所、変更方法について知りたい場合は、Codex に聞くと確認できます。
