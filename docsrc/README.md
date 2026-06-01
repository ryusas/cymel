# cymel 多言語（日本語・英語）ドキュメント構築メモ

このディレクトリ（docsrc/）は、cymel のドキュメントを多言語（日本語・英語）でビルドするための環境。
Sphinxの国際化（i18n）機能、sphinx-intl、および自動翻訳スクリプトを用いて、日本語のドキュメントソースから英語版のドキュメントを自動生成する。

---

## 1. 【初回のみ】開発環境の構築手順

uv を使用し、Maya 2027 の mayapy をベースとした仮想環境を構築する。

### 1-1. 仮想環境の作成
プロジェクトのルートディレクトリで以下のコマンドを実行。
```powershell
uv venv --system-site-packages --python "C:\Program Files\Autodesk\Maya2027\bin\mayapy.exe"
```
> [!NOTE]
> cymel は maya.cmds などのMaya専用ライブラリに依存しているため、仮想環境作成時に必ず --system-site-packages を指定して、Maya本体のパッケージを参照できるようにすること。

### 1-2. 依存ライブラリのインストール
仮想環境内にドキュメント構築および自動翻訳に必要なライブラリをインストール。
```powershell
uv pip install sphinx sphinx-intl polib deep-translator certifi
```

### 1-3. SSL/TLS接続エラーの対策（Windows環境）
Windows環境の mayapy 仮想環境内でHTTPS接続エラーが発生するのを防ぐため、以下のコマンドでCA証明書バンドルを強制再インストールする。
```powershell
uv pip install --force-reinstall certifi
```

---

## 2. 【随時】ソース変更時の翻訳データ更新手順

Pythonのソースコード（docstring）や、docsrc/srcs/ 下のRSTドキュメントを書き換えた後は、以下の手順で英語の翻訳データ（.po）を最新状態に同期する。

### Step 1. 日本語テキスト（Template）の再抽出
最新のドキュメントソースから、翻訳用の日本語テキスト（*.pot）を抽出。
```powershell
.venv\Scripts\python.exe -m sphinx.cmd.build -b gettext docsrc/srcs docsrc/locale
```

### Step 2. 既存の英語翻訳辞書（.po）へのマージ
抽出した最新テキストを、既存 of 英語翻訳ファイルにマージ。
```powershell
.venv\Scripts\python.exe -m sphinx_intl update -d docsrc/locale -p docsrc/locale -l en
```
> [!IMPORTANT]
> この処理により、過去に翻訳した英語（msgstr）はすべて維持され、新しく増えた日本語文だけが未翻訳として追加され、削除された文は自動で整理（コメントアウト等）される。

### Step 3. 増えた差分だけの自動翻訳実行
新しく増えた未翻訳の日本語テキストだけを、自動翻訳スクリプトで英訳。
```powershell
.venv\Scripts\python.exe docsrc/translate_po_files.py
```
* 無料Google翻訳利用時: Googleからボット判定をされないよう、適度なウェイト（0.2秒）を挟みながら、未翻訳部分だけをゆっくり自動翻訳する。
* 有償DeepLなどの利用時: my_translator.py を設定している場合は、ウェイトなしの高速で翻訳が完了する。

---

## 3. ドキュメントのクリーンビルド手順

翻訳データの同期が終わったら、以下のビルドスクリプトを実行するだけで、日本語版と英語版のHTMLドキュメントが完全にビルドされる。

```powershell
.venv\Scripts\python.exe docsrc/build_docs.py
```

### このビルドスクリプトが自動で行うこと：
* 古い成果物の全自動クリーンアップ:
  docs/ja/ および docs/en/ ディレクトリをビルド前にフォルダごと一旦完全消去し、古いHTMLがゴミとして残るのを防ぐ。
* 翻訳データの自動コンパイル:
  テキスト形式の .po ファイルから、Sphinxが読み込むバイナリ形式の .mo ファイルへのコンパイル（sphinx-intl build）を自動的に行う。
* 日・英ドキュメントの同時ビルド:
  日本語版ドキュメント（docs/ja/）と、言語設定を英語に差し替えた英語版ドキュメント（docs/en/）を同時にビルド。
* .nojekyll ファイルの自動設置:
  GitHub PagesでCSSやアセットが正常に読み込めるよう、docs/、docs/ja/、docs/en/ のそれぞれに自動で .nojekyll ファイルを作成する。

---

## 4. Git管理（コミット）のルール

リポジトリをクリーンに維持するため、コミット対象を整理する。

### コミットするべきもの（必須）
* `docsrc/locale/en/LC_MESSAGES/*.po`: 翻訳データのマスターソース（辞書）。
* `docs/ja/` および `docs/en/`: GitHub Pagesとして直接公開される成果物のHTML群。
* `docs/index.html`: 日・英それぞれのトップページへ誘導する言語選択のランディングページ。
* `docsrc/translate_po_files.py` / `docsrc/build_docs.py` / `docsrc/README.md`: ビルドや翻訳を自動化・管理するスクリプトと本メモ。

### コミットしないもの（.gitignore に登録済み）
* `docsrc/my_translator.py`: 個人用の翻訳API認証キー等。
* `*.mo`: コンパイル済みのバイナリ辞書ファイル。ビルド時に全自動生成されるため不要。
* `docsrc/locale/*.pot`: 一時生成される翻訳テンプレートファイル。再抽出可能なので不要。
* `.venv/`: Python仮想環境ディレクトリ。

---

## 5. 【オプション】有償DeepLなどのAPIキーを使って高速翻訳する

もし自身のDeepL API Pro（有償ライセンス）や、Google Cloud Translation API、自前のカスタム翻訳機を使用したい場合、docsrc/my_translator.py を作成して登録することができる。

### 設定例（DeepL API Proの場合）
docsrc/ の直下に my_translator.py を作成し、以下のように記述する。

```python
# -*- coding: utf-8 -*-
from deep_translator import DeeplTranslator

def get_translator(source='ja', target='en'):
    # 自身の DeepL 認証キー（APIキー）を指定
    # 有償 Pro プランの場合は use_free_api=False にする
    return DeeplTranslator(
        api_key="YOUR_DEEPL_API_KEY_HERE", 
        source=source, 
        target=target, 
        use_free_api=False
    )
```

このファイルを置くだけで、自動翻訳スクリプト（translate_po_files.py）が自動的に有償翻訳器を検知し、ウェイトなしの最高速（数秒〜十数秒）で翻訳を終わらせる。
このファイルは .gitignore に登録されているため、APIキーが意図せずGitにコミットされることはない。
