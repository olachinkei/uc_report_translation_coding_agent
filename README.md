# UC Report Translation Coding Agent

この repository は、ユニゾンの日本語レポートを英語レポートへ翻訳し、必要に応じて Word `.docx` まで戻すための作業場所です。

ビジネスユーザーは、基本的に **Codex に依頼するだけ** で作業を進めます。コマンド実行、ファイル変換、翻訳、レビュー、出力作成は Codex が行います。

内部構成や agent 向けの詳細は [docs/index.md](docs/index.md) にあります。通常の利用では、この README の依頼例だけ見れば十分です。

## この Repository の役割

- 新しい日本語 `.docx` を翻訳しやすい markdown `.md` に変換する
- 日本語 markdown を英語 markdown に翻訳する
- 翻訳済み markdown をレビュー・修正する
- レビュー済み markdown を Word `.docx` に変換する
- 過去レポートを translation memory として蓄積する

## できること

### 1. docx を markdown に変換する

使う skill:

- `$report-source-preparation`

Word 原稿を受け取ったら、まず元ファイルを次の場所に置きます。

```text
data/past_raw_files/
```

Codex には次のように依頼してください。

```text
data/past_raw_files/Unison Impact_J_2025.docx を、
翻訳準備用の markdown に変換してください。

出力先は data/past_markdown_files/Unison Impact_J_2025.md にしてください。
見出し構造、数値、固有名詞、表が崩れていないかも確認してください。
```

出力先:

```text
data/past_markdown_files/Unison Impact_J_2025.md
```

元の `.docx` は原本なので編集しません。Word 由来の不要なラベルや空見出しがある場合は、markdown 側だけを整えます。

### 2. markdown を英語 markdown に翻訳する

使う skill:

- `$report-translation-workflow`

翻訳対象の日本語 markdown は次の場所に置きます。

```text
data/past_markdown_files/
```

Codex には次のように依頼してください。

```text
data/past_markdown_files/Unison Impact_J_2025.md を英語に翻訳して、
outputs/drafts/Unison Impact_E_2025.md に保存してください。

過去レポート、data/knowledge、prompt.md を参照してください。
数値、年号、会社名、ファンド名、見出し構造は変えないでください。
```

出力先:

```text
outputs/drafts/Unison Impact_E_2025.md
```

翻訳後は、まずレビューを依頼してください。

```text
outputs/drafts/Unison Impact_E_2025.md を、
data/past_markdown_files/Unison Impact_J_2025.md と照合してレビューしてください。

数値、固有名詞、見出し構造、抜け漏れを重点的に見てください。
```

直接 `outputs/drafts/*.md` を編集しても構いません。大きな修正が複数ある場合は、対象 section と変更方針を分けて Codex に依頼すると安定します。

```text
outputs/drafts/Unison Impact_E_2025.md を修正してください。

1. 「Greeting」の第 3 段落を、投資家向けに少し自然で前向きな表現にしてください。
2. 「Visualization of Impact through Quantification」は 2024 年版の言い回しに寄せてください。
3. Company description は事実を変えず、少し簡潔にしてください。
4. 数値、年号、会社名、ファンド名は変更しないでください。
```

### 3. markdown から docx を作る

使う skill:

- `$report-docx-export`

レビュー済みの英語 markdown を Word に変換します。Codex には次のように依頼してください。

```text
outputs/drafts/Unison Impact_E_2025.md を Word docx に変換してください。

出力先は outputs/final/Unison Impact_E_2025.docx にしてください。
変換後、ファイルが作成されていることも確認してください。
```

出力先:

```text
outputs/final/Unison Impact_E_2025.docx
```

Word の見た目を既存テンプレートに寄せたい場合は、reference docx も一緒に指定してください。

```text
outputs/drafts/Unison Impact_E_2025.md を Word docx に変換してください。
path/to/reference.docx を reference docx として使ってください。

出力先は outputs/final/Unison Impact_E_2025.docx にしてください。
```

## メンテナンス方法

### 過去ファイルの場所

過去レポートは翻訳品質を上げるための材料です。置き場所を分けて管理します。

```text
data/past_raw_files/
```

- 過去レポートの原本 `.docx`
- 編集しない
- 監査・再変換用に保持する

```text
data/past_markdown_files/
```

- 過去レポートの markdown 化済み corpus
- heading 整理や Word ノイズ除去はここで行う
- 日英ファイルは `_J_` と `_E_` で対応させる

```text
data/knowledge/
```

- 毎年再利用する表現
- 固定訳や recurring section の説明
- `section_pairs.jsonl` は過去の日英 markdown から生成される translation memory

### 過去レポートを追加した後

日英の過去レポートを追加・修正したら、Codex に translation memory の更新を依頼してください。

```text
data/past_markdown_files に追加した過去レポートを確認し、
日英 section alignment を検証してください。

問題がなければ data/knowledge/section_pairs.jsonl を再生成し、
最後に make check まで実行してください。
```

### 出力ファイルの場所

```text
outputs/drafts/
```

- 翻訳直後の英語 markdown
- レビュー・修正対象

```text
outputs/final/
```

- 納品候補の `.docx`
- 必要なら最終版 markdown もここに置く

```text
outputs/prompts/
```

- debug 用の section prompt
- 通常利用では触らなくてよい
