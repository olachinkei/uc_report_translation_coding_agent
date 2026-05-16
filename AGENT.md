# AGENT.md

この文書は AI Agent / 開発者向けの内部ドキュメントです。

ビジネスユーザー向けの概要は [README.md](README.md) を参照してください。

## 1. 目的

このリポジトリは、過去の日英レポートを再利用しながら、新しい日本語 markdown レポートを英語 markdown に翻訳するための実装基盤です。

狙いは逐語訳ではなく、過去に繰り返し現れた表現を translation memory と curated knowledge として再利用し、章ごとの文脈を保ちながら英訳することです。

## 2. フォルダ構成

```text
.
├── AGENT.md
├── README.md
├── prompt.md
├── data
│   ├── past_raw_files
│   ├── past_markdown_files
│   └── knowledge
└── skills
    ├── report-source-preparation
    │   └── SKILL.md
    ├── report-translation-workflow
    │   ├── SKILL.md
    │   └── scripts
    │       └── prepare_translation_prompt.py
    └── translation-memory-builder
        ├── SKILL.md
        └── scripts
            ├── extract_section_pairs.py
            └── validate_corpus_alignment.py
```

### 主要ファイルの役割

- `prompt.md`
  - 翻訳時のベースプロンプト
  - 固定訳辞書もここに集約する
- `data/past_raw_files`
  - 過去レポートの raw Word `.docx`
  - 原本置き場であり、通常は編集しない
- `data/past_markdown_files`
  - 翻訳再利用用の markdown corpus
  - heading 正規化や Word ノイズ除去の編集対象はここ
- `data/knowledge`
  - 再利用価値の高い知識断片
  - `section_pairs.jsonl` もここに置く

## 3. Skills 構成

このリポジトリでは skill を 3 本に分けています。

### `report-source-preparation`

役割:

- raw Word または markdown 原稿を翻訳入力用の markdown に整える
- 見出し構造を保ちつつ Word 由来のノイズを除く

使う場面:

- 新しい `.docx` を受け取った直後
- markdown 変換直後に heading が弱いとき

### `translation-memory-builder`

役割:

- 過去日英 corpus を整備する
- heading のずれを見つける
- section pair を再構築する
- `data/knowledge` の更新対象を見つける

使う場面:

- 新しい過去レポートを追加したとき
- retrieval 精度を上げたいとき
- 2021/2022 のように heading 正規化を進めたいとき

### `report-translation-workflow`

役割:

- 新しい markdown の翻訳実行
- section ごとの類似例検索
- prompt 組み立て
- 部分修正

使う場面:

- 新しい翻訳案件の実行
- 特定 section だけの再翻訳
- 修正指示の反映

## 4. Markdown 変更方針

markdown corpus を編集するときは、`past_raw_files` の raw docx は触らず、`data/past_markdown_files` 側だけを整える。

### 基本ルール

- 事実、数値、固有名詞、年号は変えない
- 原文の意味を変える要約や意訳はしない
- heading は retrieval を改善するために必要な範囲で追加・正規化してよい
- Word 由来のノイズは落としてよい
- 原本の見出しが弱い場合は、本文構造から推定して heading を与えてよい
- 日英で対応する section がある場合は、section の粒度をそろえる

### 正規化の対象

- `ESG の位置付け` のような不自然な空白
- `【第2 段階】` と `【第二段階】` のような表記ゆれ
- `前文説明書き`、`キャプチャ①`、`コンテンツ・タイトル` のような Word 由来のラベル
- `x` や `×` だけの行
- 空見出し、画像だけの section、目次相当 section

### 追加 heading の考え方

追加 heading は、translation memory と retrieval の改善に直結する場合に限って入れる。

具体例:

- `Raviプロフィール` の中に混在していた platform progress を別 section に切る
- 同名 heading が連続していた精神科パートを `N・フィールド`、`岡本病院・共和薬品`、`CHCPグループ` といった固有名つき heading に分ける
- 1 section に混ざっていた Sukesan インタビューと CHCP の医療パートを分離する

## 5. オフライン整備

ここでいうオフライン整備とは、LLM を呼ばずに corpus と knowledge をメンテナンスする作業です。

### 基本フロー

1. raw docx を `data/past_raw_files` に置く
2. markdown に変換して `data/past_markdown_files` に置く
3. heading を整える
4. 日英の section alignment を確認する
5. `section_pairs.jsonl` を再構築する
6. 必要なら `data/knowledge/*.txt` と `prompt.md` の辞書を更新する

### オフライン整備で使うスクリプト

#### section pair の再構築

```bash
python3 skills/translation-memory-builder/scripts/extract_section_pairs.py \
  --corpus-dir data/past_markdown_files \
  --output data/knowledge/section_pairs.jsonl
```

#### alignment の点検

```bash
python3 skills/translation-memory-builder/scripts/validate_corpus_alignment.py \
  --corpus-dir data/past_markdown_files
```

### knowledge 更新の判断

`data/knowledge` に入れるもの:

- 毎年類似する greeting
- ESG framework の説明
- impact quantification / visualization の説明
- afterword / feedback request

`data/knowledge` に入れないもの:

- 単年しか出ない case study の細部
- 一度しか出ない数字
- 画像キャプションだけの情報
- corpus 本体で十分に引ける長文

## 6. Python のコードを使った実装方式

Python 実装は、offline preparation と translation execution を分けています。

### 6.1 Offline preparation

#### `extract_section_pairs.py`

役割:

- markdown を heading ベースで section に分割
- preface/noise section を除外
- 日英ペアを index ベースで対応付け
- `section_pairs.jsonl` を生成

実装ポイント:

- heading 行は `#` の数で section level を取る
- body は `clean_body()` でラベルやノイズを除く
- `labels` を付けて greeting / framework / quantification / credit などを推定する

#### `validate_corpus_alignment.py`

役割:

- 各年の日英 markdown の section 数と heading 対応を確認する
- corpus 更新時の回帰チェックに使う

### 6.2 Translation execution

#### `prepare_translation_prompt.py`

役割:

- 入力 markdown から対象 section を探す
- 前後 section を context として取る
- `section_pairs.jsonl` と `data/knowledge` を検索する
- 類似例と knowledge を埋め込んだ section prompt を生成する

実装ポイント:

- query/candidate の token overlap に heading bonus を加えて score を付ける
- heading の normalize / fuzzy match を使う
- knowledge 側にも `greeting` や `quantification` の bonus を付ける
- source markdown 側でも preface/noise section を落として context を安定化させる

#### Codex 翻訳

役割:

- 入力 markdown を section ごとに翻訳する
- `prepare_translation_prompt.py` や `prompt.md` の考え方を使って、過去例と curated knowledge を参照する
- 出力 `.md` を `outputs/drafts/` に書く

入出力ルール:

- 入力: `data/past_markdown_files` の日本語 markdown
- 出力: `outputs/drafts/` の英語 markdown
- 既定では `_J_` を `_E_` に置換したファイル名にする

### 6.3 実装上の前提

- translation memory の中心は `data/knowledge/section_pairs.jsonl`
- curated phrasing は `data/knowledge/*.txt`
- base prompt と辞書は `prompt.md`
- markdown corpus の品質が retrieval 品質を大きく左右する

## 7. Agent が作業するときの優先順

1. raw file は保持し、markdown corpus 側で整える
2. まず alignment を壊さない
3. 次に retrieval 品質が上がる heading 正規化を行う
4. その上で `section_pairs.jsonl` を再生成する
5. 翻訳品質に recurring な改善が見つかったら `data/knowledge` または `prompt.md` に反映する

## 8. 変更時の注意

- `data/past_raw_files` は監査用の原本として扱う
- corpus 修正後は `validate_corpus_alignment.py` を回す
- memory 再生成後は `section_pairs.jsonl` の件数と主要 section の当たり方を確認する
- ビジネスユーザー向けの説明は `README.md` に集約し、内部詳細はこの `AGENT.md` に寄せる
