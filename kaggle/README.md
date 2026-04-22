---
title: "Claude Code × Kaggle: WSL + uv + VSCode で回す開発ワークフロー"
emoji: "🏆"
type: "tech"
topics: ["kaggle", "claudecode", "uv", "python", "wsl"]
published: false
---

# Claude Code × Kaggle: WSL + uv + VSCode で回す開発ワークフロー

## はじめに

このガイドでは、**WSL 上の VSCode** を起点として、Claude Code を使いながら Kaggle コンペに挑戦するワークフローを整理します。Python 環境は `uv` で統一し、秘密情報を GitHub に漏らさない設計も込みで一通り説明します。

完成したときのイメージはこんな感じです。

```
WSL (Ubuntu)
  └─ VSCode (Remote-WSL で起動)
       ├─ Claude Code (ターミナルで起動 → ペアプロ相手として使う)
       ├─ uv 環境 (pyproject.toml / uv.lock で再現性を保証)
       ├─ Kaggle CLI (コンペ情報取得・提出)
       └─ gh (GitHub へ push・repo 管理)
```

**前提読者**: WSL / Kaggle / uv のどれかを少し触ったことがある方。Claude Code は初めてでも大丈夫です。

> 📸 スクショ: 完成後の VSCode ウィンドウ全体（左に Explorer、下に Claude Code ターミナル）

<img width="615" height="561" alt="image" src="https://github.com/user-attachments/assets/1feb2cbc-24a1-4fde-9750-74d06f146bdc" />


---

## 1. 前提環境の確認

以下のツールが WSL 側に入っていることを確認してください。バージョンは 2025 年時点の動作確認値です。

| ツール | バージョン | インストール方法 |
|--------|-----------|-----------------|
| WSL2 (Ubuntu 22.04+) | — | Microsoft 公式ドキュメント参照 |
| Git | 2.x 以上 | `sudo apt install git` |
| uv | 0.10 以上 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| gh | 2.x 以上 | `sudo apt install gh` |
| Node.js | 18 以上 | nvm 経由推奨 |
| Claude Code | 最新 | `npm install -g @anthropic-ai/claude-code` |
| VSCode | 最新 | Windows 側にインストール + Remote-WSL 拡張 |

Git の初期設定:

```bash
git config --global user.name "Your Name"
git config --global user.email "your@example.com"
```

---

## 2. WSL から VSCode を開く

ターミナル (WSL) でコンペ用ディレクトリを作り、VSCode をそこから起動します。

```bash
mkdir -p ~/programming/work/kaggle/<competition-name>
cd ~/programming/work/kaggle/<competition-name>
code .
```

`<competition-name>` は Kaggle 上のコンペスラグ（例: `titanic`）に合わせると管理が楽です。

> 📸 スクショ: VSCode 左下に「WSL: Ubuntu」と表示されている様子

VSCode のステータスバー左下が **「WSL: Ubuntu」** になっていれば Remote-WSL として正しく開いています。ここ以降の操作は VSCode 内のターミナルで行います。

---

## 3. uv で Python プロジェクトを初期化する

```bash
uv init --python 3.11
```

これで `pyproject.toml` / `uv.lock` / `.python-version` が生成されます。次に必要なライブラリを追加します。

```bash
# 本番依存
uv add kaggle pandas numpy scikit-learn polars lightgbm

# 開発用ツール
uv add --dev ruff pytest ipykernel jupyter
```

**各ファイルの役割:**

| ファイル | 役割 |
|----------|------|
| `pyproject.toml` | 依存宣言・プロジェクトメタデータ |
| `uv.lock` | 依存の完全なスナップショット（必ずコミットする） |
| `.venv/` | 仮想環境本体（`.gitignore` に追加する） |

Kaggle Notebook 環境に Python バージョンを揃えたい場合:

```bash
uv python pin 3.10   # Kaggle は 2025 時点で 3.10 が主流
```

---

## 4. Kaggle CLI のセットアップ（秘密情報の置き場所）

### 4-1. API トークンの取得

Kaggle のアカウントページ ([kaggle.com/settings](https://www.kaggle.com/settings)) を開き、**"Create New Token"** をクリックします。`kaggle.json` がダウンロードされます。

> 📸 スクショ: Kaggle アカウントページの "API" セクション

### 4-2. kaggle.json の配置

```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```

**重要**: `~/.kaggle/` はホームディレクトリ直下です。**プロジェクトリポジトリの中に置かないでください。**

### 4-3. 動作確認

```bash
uv run kaggle competitions list
```

リストが表示されれば認証成功です。

### 4-4. 環境変数での認証（CI 用途向け代替）

CI 環境など `kaggle.json` を置けない場所では、環境変数で認証できます:

```bash
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=xxxxxxxxxxxxxxxx
uv run kaggle competitions list
```

---

## 5. セキュリティ設計 — GitHub に上げないもの

### 5-1. .gitignore を作る

プロジェクトルートに `.gitignore` を作成します:

```gitignore
# Python 環境
.venv/
__pycache__/
*.py[cod]
.pytest_cache/

# データ・成果物（サイズが大きく、コンペ規約上 Git 管理しない）
data/
runs/
submissions/
*.csv
*.zip
*.parquet
*.feather

# 秘密情報（絶対に上げない）
.env
.env.*
kaggle.json
.kaggle/

# OS・エディタ
.DS_Store
.idea/
.vscode/settings.json
```

### 5-2. .env ファイルの使い方

スクリプトから環境変数を参照したい場合は `.env` を使います。`.env` 自体は **絶対にコミットしない**。

```bash
# .env (例)
KAGGLE_USERNAME=your_username
KAGGLE_KEY=xxxxxxxxxxxxxxxx
```

`python-dotenv` をインストールしなくても、`uv run` に `--env-file` オプションを使えます:

```bash
uv run --env-file .env python src/train.py
```

### 5-3. コミット前の自己点検チェックリスト

push 前に必ず以下を確認してください:

```bash
# 1. ステージされているファイルを確認
git status
git diff --cached --name-only

# 2. 秘密情報が含まれていないか grep で確認
grep -rn "KAGGLE_KEY\|kaggle.json\|api_key\|password" \
  . --exclude-dir=.venv --exclude-dir=.git || echo "秘密情報なし"

# 3. data/ や submissions/ が含まれていないか確認
git diff --cached --name-only | grep -E "^(data|submissions|runs)/" || echo "OK"
```

### 5-4. GitHub の Push Protection を有効化する

GitHub 側でも秘密情報の push をブロックできます。リポジトリ作成後に有効化を推奨します:

- リポジトリの **Settings → Code security and analysis → Secret scanning → Push protection** を ON に。

---

## 6. コンペ情報の取得

```bash
# コンペを検索
uv run kaggle competitions list --search "tabular"

# データをダウンロード（data/ は .gitignore 済み）
uv run kaggle competitions download -c <competition-slug> -p data/

# 解凍
unzip -d data/ data/<competition-slug>.zip
```

**規約同意を忘れずに:** 初回は Kaggle Web UI でコンペの規約に同意が必要です。未同意の状態で download すると `403 Forbidden` が返ります。

> 📸 スクショ: Kaggle Web UI の "I Understand and Accept" ボタン

---

## 7. VSCode 上で Claude Code を起動して開発する

### 7-1. Claude Code の起動と初期設定

VSCode のターミナルで:

```bash
claude
```

初回起動時にブラウザで Anthropic への認証が求められます。完了するとプロンプトが表示されます。

次に `/init` コマンドでプロジェクト固有のルールファイル (`CLAUDE.md`) を生成します:

```
> /init
```

生成された `CLAUDE.md` を開き、プロジェクト固有のルールを追記します:

```markdown
## このプロジェクトのルール

- Python 環境は uv のみを使う。pip / poetry / conda は使わない
- 依存の追加は `uv add <package>` で行う
- `data/` ディレクトリはコミットしない（コンペ規約 + サイズ）
- 実験結果は `runs/<YYYYMMDD_HHMMSS>_<experiment-name>/` に保存する
- 予測 CSV は `submissions/<YYYYMMDD>_<model>_<note>.csv` として保存する
- 乱数シードは `SEED = 42` で統一する
```

### 7-2. 典型的な開発フロー

**ステップ 1: データを確認する**

Claude Code に以下のように依頼します:

```
train.csv と test.csv を読み込んで、shape / dtypes / describe / 欠損値の状況を
pandas でまとめて表示するスクリプトを src/check_data.py に作ってください。
実行は uv run python src/check_data.py でできるようにしてください。
```

**ステップ 2: EDA ノートブックを作る**

```
notebooks/01_eda.ipynb を作成し、
- 目的変数の分布
- 特徴量ごとの欠損率
- 目的変数との相関ヒートマップ
を可視化するセルを追加してください。データは data/ から読んでください。
```

**ステップ 3: ベースラインモデルを作る**

```
LightGBM で 5-Fold CV を回すベースライン学習スクリプトを src/train.py に作ってください。
条件:
- SEED = 42 を定数として定義する
- CV スコアをターミナルに出力する
- 予測 CSV を submissions/ に <YYYYMMDD>_lgbm_baseline.csv として保存する
- uv run python -m src.train で実行できるようにする
```

**ステップ 4: Plan モードを活用する**

大きな変更（特徴量エンジニアリング全体の設計、リファクタリングなど）は `/plan` を使って事前に設計を見てから実行します:

```
> /plan
```

### 7-3. サブエージェントの使い分け

Claude Code は内部でサブエージェントを使って並列作業できます。以下を使い分けます:

- **通常会話**: 1 ファイルへの小さな変更、コードの説明
- **`/plan` モード**: 設計の承認が必要な大きな変更
- **Explore エージェント**: `「src/ 配下で〇〇を使っているファイルを探して」` のようなコードベース探索

---

## 8. 推奨ディレクトリ構成と再現性の確保

### 8-1. ディレクトリ構成

```
<competition-name>/
├── pyproject.toml          # uv プロジェクト設定
├── uv.lock                 # 依存スナップショット（コミット必須）
├── .python-version         # Python バージョン固定
├── .gitignore
├── CLAUDE.md               # Claude Code 向けルール
├── README.md               # コンペ概要・実行手順・スコア記録
├── src/
│   ├── __init__.py
│   ├── check_data.py
│   ├── train.py
│   └── predict.py
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_feature_engineering.ipynb
├── kernels/                # Kaggle Notebook 提出用（後述）
│   ├── kernel-metadata.json
│   └── main.ipynb
├── data/                   # gitignore（コンペデータ）
├── runs/                   # gitignore（モデル・ログ・設定）
│   └── 20260422_120000_lgbm_baseline/
│       ├── config.yaml
│       ├── cv_scores.txt
│       └── model.pkl
└── submissions/            # gitignore（提出 CSV）
    └── 20260422_lgbm_v1.csv
```

### 8-2. 再現性のために

- **乱数シード**: `SEED = 42` を `src/train.py` の定数として定義し、`numpy` / `random` / `lightgbm` に渡す。
- **実験条件の記録**: 各 `runs/<run_id>/` に `config.yaml` を置き、使用特徴量・ハイパーパラメータを残す。
- **`uv.lock` のコミット**: これがあれば `uv sync` で完全に同一の環境を再現できる。

---

## 9. Kaggle に提出する

### 9-1. CSV 提出（テーブルコンペ等）

```bash
uv run kaggle competitions submit \
  -c <competition-slug> \
  -f submissions/20260422_lgbm_v1.csv \
  -m "LightGBM baseline, 5-Fold CV=0.812"
```

提出履歴を確認:

```bash
uv run kaggle competitions submissions -c <competition-slug>
```

### 9-2. Notebook 提出（Code Competition）

Code Competition（Notebook 上で推論を完結させる形式）は `kaggle kernels push` を使います。

**kernels ディレクトリの準備:**

```bash
mkdir kernels
uv run kaggle kernels init -p kernels/
```

生成された `kernels/kernel-metadata.json` を編集します:

```json
{
  "id": "<kaggle-username>/<kernel-slug>",
  "title": "<コンペ名> Baseline",
  "code_file": "main.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": true,
  "enable_gpu": false,
  "enable_internet": false,
  "dataset_sources": [],
  "competition_sources": ["<competition-slug>"],
  "kernel_sources": []
}
```

`kernels/main.ipynb` に推論コードを書いたら push します:

```bash
uv run kaggle kernels push -p kernels/
```

ステータス確認:

```bash
uv run kaggle kernels status <kaggle-username>/<kernel-slug>
```

**Code Competition の注意点:**
- データは `/kaggle/input/<competition-slug>/` から読む（`data/` ではない）。
- インターネットアクセスは基本 OFF のため、モデルのダウンロードは事前に Dataset として登録する。
- GPU は必要な場合のみ `"enable_gpu": true` にする（実行時間制限あり）。

---

## 10. GitHub にコードを公開する

### 10-1. 公開前の最終確認

```bash
# ステージ状況の確認
git status

# 秘密情報が含まれていないか確認
grep -rn "KAGGLE_KEY\|kaggle.json\|api_key" \
  . --exclude-dir=.venv --exclude-dir=.git || echo "秘密情報なし"

# data / runs / submissions が含まれていないか確認
git diff --cached --name-only | grep -E "^(data|runs|submissions)/" \
  && echo "警告: 除外すべきファイルが含まれています" || echo "OK"
```

### 10-2. 初回 push

```bash
# GitHub 認証（ブラウザが開く）
gh auth login

# Git 初期化
git init
git add \
  .gitignore \
  pyproject.toml \
  uv.lock \
  .python-version \
  CLAUDE.md \
  README.md \
  src/ \
  notebooks/ \
  kernels/

git commit -m "chore: initial kaggle workspace scaffold"

# GitHub にリポジトリを作って push
gh repo create <repo-name> --public --source=. --remote=origin --push
```

### 10-3. README に書くべき内容

GitHub の `README.md` には最低限以下を書きます（Zenn の記事とは別物）:

```markdown
# <Competition Name>

## スコア
| 日付 | モデル | CV | LB |
|------|--------|----|----|
| 2026-04-22 | LightGBM baseline | 0.812 | 0.805 |

## セットアップ

```bash
uv sync
uv run kaggle competitions download -c <slug> -p data/
unzip -d data/ data/<slug>.zip
```

## 学習・提出

```bash
uv run python -m src.train
uv run kaggle competitions submit -c <slug> -f submissions/<file>.csv -m "<note>"
```
```

### 10-4. GitHub の Push Protection を確認

**Settings → Code security and analysis → Secret scanning → Push protection** が ON になっているか確認します。万が一秘密情報を含む commit を push しようとすると GitHub 側でもブロックされます。

---

## 11. GitHub Actions で自動提出する（Optional）

ローカルでの提出で十分な場合はスキップしてください。長期コンペで定期的に再学習・再提出したい場合に役立ちます。

### 11-1. GitHub Secrets に認証情報を登録

リポジトリの **Settings → Secrets and variables → Actions** で以下を追加:

- `KAGGLE_USERNAME`: Kaggle ユーザー名
- `KAGGLE_KEY`: Kaggle API キー（`kaggle.json` の `key` の値）

### 11-2. ワークフローの例

`.github/workflows/submit.yml` を作成:

```yaml
name: Kaggle Submit

on:
  workflow_dispatch:
    inputs:
      message:
        description: "提出メッセージ"
        required: true
        default: "auto submit"

jobs:
  submit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Install dependencies
        run: uv sync --frozen

      - name: Train and predict
        run: uv run python -m src.train
        env:
          KAGGLE_USERNAME: ${{ secrets.KAGGLE_USERNAME }}
          KAGGLE_KEY: ${{ secrets.KAGGLE_KEY }}

      - name: Submit to Kaggle
        run: |
          FILE=$(ls -t submissions/*.csv | head -1)
          uv run kaggle competitions submit \
            -c <competition-slug> \
            -f "$FILE" \
            -m "${{ github.event.inputs.message }}"
        env:
          KAGGLE_USERNAME: ${{ secrets.KAGGLE_USERNAME }}
          KAGGLE_KEY: ${{ secrets.KAGGLE_KEY }}
```

---

## 12. Zenn に投稿する

このファイル自体が Zenn 記事の原稿です。以下の手順で投稿します。

### 12-1. zenn-cli のセットアップ

```bash
npm install -g zenn-cli
```

Zenn のコンテンツ管理用リポジトリを別途作るか、既存リポジトリの `articles/` 配下に本ファイルを配置します:

```bash
# Zenn 管理リポジトリ (例: ~/programming/zenn-contents)
npx zenn new:article --slug kaggle-claudecode-workflow
# 生成された articles/kaggle-claudecode-workflow.md に本ファイルの内容をコピー
```

### 12-2. プレビューで確認

```bash
npx zenn preview
```

ブラウザで `http://localhost:8000` を開いてレイアウトを確認します。

### 12-3. GitHub 連携で公開

1. [zenn.dev](https://zenn.dev) の Dashboard → "GitHubからのデプロイ" で連携リポジトリを設定
2. 記事の frontmatter を `published: true` に変更
3. `git push` → Zenn 側で自動的に公開される

---

## 13. トラブルシュート

### `403 Forbidden` が出る

コンペの規約に同意していない可能性があります。Kaggle Web UI でコンペのページを開き、**"I Understand and Accept"** をクリックしてから再試行してください。

### `kaggle.json` の permission 警告

```
Warning: Your Kaggle API key is readable by other users on this system!
```

以下で解決します:

```bash
chmod 600 ~/.kaggle/kaggle.json
```

### uv で CUDA 版 PyTorch を入れたい

```bash
uv add torch --index-url https://download.pytorch.org/whl/cu121
```

Kaggle Notebook の CUDA バージョンに合わせてインデックス URL を調整してください。

### Kernel push で `code_file not found`

`kernel-metadata.json` の `code_file` は `-p` で指定したディレクトリからの**相対パス**です。

```json
// kernels/ を -p で指定する場合
{ "code_file": "main.ipynb" }   // ✅ kernels/main.ipynb を指す
{ "code_file": "kernels/main.ipynb" }  // ❌ 二重パスになる
```

### VSCode で `.venv` が認識されない

コマンドパレット (`Ctrl+Shift+P`) → **"Python: Select Interpreter"** → `.venv/bin/python` を選択してください。

### Claude Code が `uv` を見つけられない

VSCode のターミナルで `which uv` を実行して確認します。見つからない場合は `~/.bashrc` / `~/.zshrc` に `PATH` が追加されているか確認します:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## まとめ

全体フローを振り返ります:

1. **WSL で作業ディレクトリを作り `code .` で VSCode を開く**
2. **`uv init` + `uv add` で Python 環境を構築**（pip / conda は使わない）
3. **`~/.kaggle/kaggle.json` を置いて Kaggle CLI を使えるようにする**（リポジトリ外に置く）
4. **`.gitignore` で `data/` / `submissions/` / 秘密情報を除外する**
5. **VSCode ターミナルで `claude` を起動し、EDA → 学習 → 提出 CSV 生成をペアプロ**
6. **`kaggle competitions submit` または `kaggle kernels push` で Kaggle に提出**
7. **公開前チェック → `gh repo create` で GitHub に push**

秘密情報（`kaggle.json` / `.env`）はホームディレクトリまたは GitHub Secrets に置き、**絶対にリポジトリに含めない**ことが最重要です。

---

## 参考リンク

- [Kaggle API Documentation](https://www.kaggle.com/docs/api)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Zenn Contents Guide](https://zenn.dev/zenn/articles/zenn-cli-guide)
- [GitHub Secret scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)



```
不要
--------------------------------------------------------------------------------------------

## Kaggleの開発環境構築手順（uvで環境構築）
1. github上にプロジェクトを作成する（Kaggle配下）
2. WSLから```code .```でVSCodeを開く
3. このリポジトリをクローンし、1.で作成したプロジェクトに移動する
4. git init でUV環境を構築する

## 注意事項
- 必ず各コンペ用のプロジェクト毎独立してUV環境を構築する
  - kaggleリポジトリと同階層でuv init をして上位フォルダにtomlファイルが作成されてしまうと、配下のUVと競合してエラーが頻発する

## other
- KaggleのデータをstreamlitでWebアプリ化
```
