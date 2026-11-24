# GitHub授業開発活動分析ツール

授業で使用する複数のGitHubリポジトリについて，**コミット履歴の取得・AIによる作業メモ作成**と，**班別・開発者別の集計・可視化**を行うためのツールです．

## 1．2つのプログラムの役割

| プログラム | 役割 | 入力 | 出力 |
|---|---|---|---|
| `github_activity.py` | GitHubからコミット履歴を取得し，変更ファイル・変更量を集計．`--ai`指定時はコード差分等を使ってAI作業メモを作成 | GitHub URL，`repositories.json`，`repositories.txt` | 班別の`*_commits.csv`，`*_authors.csv`，`*_daily.csv`，`*_report.json`等 |
| `summarize_github_class.py` | 取得済みの班別CSVを読み込み，開発者別・班別に集計し，ダッシュボードを作成 | `github_report/`配下の`*_commits.csv` | `students_summary.csv`，`students_commits.csv`，`teams_summary.csv`，`dashboard.html` |

**処理の順番**：`repositories.json` → `github_activity.py` → `github_report/<班名>/<班名>_commits.csv` → `summarize_github_class.py` → `github_report/_class_summary/`．

> `summarize_github_class.py`はGitHubに再接続せず，OpenAI APIも呼び出しません．既存CSVを何度でも再集計できます．

## 2．推奨フォルダ構成

```text
GitHubAnalysis/
├── github_activity.py
├── summarize_github_class.py
├── repositories.json
├── repositories.txt           # JSONを使う場合は不要
├── aliases.example.json      # 名寄せが必要な場合のみ使用
├── .env                      # AI要約時のAPIキー（公開禁止）
├── .gitignore
└── github_report/            # 実行時に作成
    ├── team01/
    │   ├── team01_commits.csv
    │   ├── team01_authors.csv
    │   ├── team01_daily.csv
    │   └── team01_report.json
    ├── team02/
    │   └── team02_commits.csv
    └── _class_summary/
        ├── students_summary.csv
        ├── students_commits.csv
        ├── teams_summary.csv
        └── dashboard.html
```

実際に生成される班別ファイルは，使用する`github_activity.py`のバージョン・設定によって異なる場合があります．

## 3．動作環境

- Python 3.9以降を推奨．
- Git（`git --version`で確認）．
- `github_activity.py`のAI要約を利用する場合はOpenAI APIキーが必要です（API利用料金が発生します）．
- `summarize_github_class.py`はPythonの標準ライブラリのみで動作します．

`.env`を読み込む`github_activity.py`では，必要に応じて以下を実行します．

```bash
pip install python-dotenv
```

`.env`はPythonファイルと同じ場所に置きます．

```dotenv
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

`.gitignore`の例：

```gitignore
.env
__pycache__/
```

APIキーをコード・CSV・GitHubに公開しないでください．非公開リポジトリの差分をAIに送信する際は，秘密情報の混入にも注意してください．

## 4．分析対象のリポジトリを登録

### JSON形式（推奨）

`repositories.json`：

```json
{
  "repositories": [
    {"name": "team01", "url": "https://github.com/OWNER/REPO1"},
    {"name": "team02", "url": "https://github.com/OWNER/REPO2"}
  ]
}
```

`name`には班番号や班名を指定します．出力フォルダ・ファイル名の共通名として使用されます．

### TXT形式

`repositories.txt`：

```text
team01	https://github.com/OWNER/REPO1
team02	https://github.com/OWNER/REPO2
```

班名とURLはタブで区切ります．URLだけの行にも対応する設計です．

## 5．STEP 1：GitHub履歴の取得とAI要約

JSONに登録したリポジトリを一括取得します．

```bash
python github_activity.py --input repositories.json --ai
```

TXTの場合：

```bash
python github_activity.py --input repositories.txt --ai
```

期間を指定する場合：

```bash
python github_activity.py --input repositories.json --ai --since 2026-09-01 --until 2026-11-24
```

AIなしで履歴だけ取得する場合：

```bash
python github_activity.py --input repositories.json
```

少数のコミットに絞ってAI要約を試す場合：

```bash
python github_activity.py --input repositories.json --ai --max-ai-commits 5
```

**AIによる作業メモの性質**：コミットメッセージ・変更ファイル・コード差分から推定した説明です．差分に現れない作業や意図を断定するものではありません．生成済みメモは班別CSVに保存され，STEP 2で再利用します．

## 6．STEP 2：各班CSVを開発者別に集計

```bash
python summarize_github_class.py --input github_report
```

期間指定：

```bash
python summarize_github_class.py --input github_report --since 2026-09-01 --until 2026-11-24
```

出力先指定：

```bash
python summarize_github_class.py --input github_report --output report_results
```

HTMLに表示する開発者ごとの作業メモ数を増やす場合：

```bash
python summarize_github_class.py --input github_report --memo-limit 15
```

### 学生の名寄せ

同じ学生が複数のメールアドレスや名前でコミットしている場合，別人として数えられることがあります．

`aliases.example.json`を参考に，名寄せJSONを作成します．

```json
{
  "student01@example.com": "学生A",
  "student01@users.noreply.github.com": "学生A"
}
```

```bash
python summarize_github_class.py --input github_report --aliases aliases.example.json
```

名寄せしない場合は，基本的にコミットのメールアドレス単位で集計します．

## 7．集計結果

省略時の出力先は`github_report/_class_summary/`です．

| ファイル | 主な項目 | 用途 |
|---|---|---|
| `students_summary.csv` | 班名，開発者，メールアドレス，コミット数，活動日数，追加・削除行数，変更ファイル種類数，初回・最終活動日，主な作業分類，作業メモ抜粋 | 学生ごとの活動量比較 |
| `students_commits.csv` | 班名，開発者，日時，SHA，作業分類，作業メモ，変更ファイル，行数，コミットURL | 各学生の具体的な作業内容の確認 |
| `teams_summary.csv` | 班名，開発者数，コミット数，追加・削除行数，最多コミット者の割合 | 班別の活動比較 |
| `dashboard.html` | 班別の学生カード，コミット数バー，活動量，最近の作業メモ | ブラウザでの可視化 |

`dashboard.html`はダブルクリックで表示できます．班名や開発者名で絞り込みできます．

## 8．よくあるエラー

### `_csv.Error: field larger than field limit (131072)`

AIメモなどが長く，CSVの1フィールドが標準の読み込み上限を超えた場合に発生します．**本READMEと一緒に配布している更新版`summarize_github_class.py`には修正済み**です．

旧版を利用する場合は`import csv`と`import sys`を追加した上で，CSV読み込み前に次を実行してください．

```python
limit = sys.maxsize
while True:
    try:
        csv.field_size_limit(limit)
        break
    except OverflowError:
        limit //= 10
```

### `必要な列がありません`

`*_commits.csv`に必要な列がない場合のエラーです．現在の集計プログラムでは以下の列が必要です．

`開発者`，`メールアドレス`，`日時`，`作業メモ`，`変更ファイル一覧`，`追加行数`，`削除行数`

`github_activity.py`から生成されたCSVか，見出しが変更されていないか確認してください．

### GitHubへのアクセスに失敗する

`git --version`でGitの存在を確認してください．非公開リポジトリの取得には，認証と対象リポジトリへの権限が必要です．

### AI要約されない

`.env`，`OPENAI_API_KEY`，`--ai`指定，利用可能なAPI残高・モデル設定を確認してください．AIなしのモードでは簡易メモが使用されます．

## 9．授業評価に利用する際の注意

- **コミット数・変更行数＝貢献度ではありません**．大きなファイルの自動生成，整形作業などで行数が増える場合があります．
- コミット記録だけでは，設計，会議，口頭での相談，コードレビュー，テスト作業などは測定できません．
- 開発者名・メールアドレスはGitの設定に依存します．同一人物の名寄せと，共用アカウントの有無の確認が必要です．
- 元の収集プログラムは原則としてデフォルトブランチの非マージコミットを対象とするため，未マージブランチ等の活動は抜ける可能性があります．
- AI作業メモは推定です．重要な判断にはコミットURLから差分を確認してください．
- 提出物と面談・自己評価を組み合わせ，授業成績を自動確定するための唯一の根拠にはしないでください．

## 10．日常的な運用

1. 各班のURLを`repositories.json`に登録する．
2. 週末や授業終了時に`github_activity.py`で履歴を更新する．
3. `summarize_github_class.py`を実行する．
4. `dashboard.html`を確認し，必要に応じて`students_summary.csv`をExcelで開く．
5. 成績評価前には，名寄せ，AIメモ，GitHub上の実際の変更を確認する．

---

このREADMEは両プログラムを一緒に運用することを想定しています．`github_activity.py`の実際のバージョンによって，使用できるオプションと出力ファイル名は多少異なる可能性があります．

## 11．BATファイルによる実行（Windows）

次の3ファイルを，2つのPythonプログラムと同じフォルダに置きます．**BATファイルはダブルクリックで実行できます**．実行時はBATファイルのあるフォルダを基準に処理するため，OneDriveなどの別ドライブに配置しても使用できます．

| BATファイル | 処理 | 使用場面 |
|---|---|---|
| `01_github_activity.bat` | `github_activity.py --input repositories.json --ai` | GitHubの最新履歴を取得してAI作業メモを作成 |
| `02_summarize_github_class.bat` | `summarize_github_class.py --input github_report` | 既存CSVだけを再集計して，ダッシュボードを表示 |
| `03_run_all.bat` | ①と②を順番に実行 | 最新履歴取得から授業用レポート生成まで一括実行 |

### 推奨フォルダ構成

```text
GitHubAnalysis/
├── github_activity.py
├── summarize_github_class.py
├── 01_github_activity.bat
├── 02_summarize_github_class.bat
├── 03_run_all.bat
├── repositories.json
├── .env
└── github_report/
```

### 実行前の確認

- コマンドプロンプトで `python --version` と `git --version` が動作すること．
- AI要約を使う場合，`.env`に`OPENAI_API_KEY`を設定しておくこと．
- `.env`の読み込みに`python-dotenv`を使っている場合，そのライブラリをインストールしておくこと．
- WindowsでPythonをConda環境にのみインストールしている場合，**エクスプローラーからのダブルクリックではその環境が自動で有効になりません**．その場合はAnaconda Promptで`conda activate 環境名`を実行してから，該当BATを起動してください．

BATは処理失敗時にメッセージを表示して停止します．`02`と`03`は集計完了後，`github_report/_class_summary/dashboard.html`が存在すればブラウザで開きます．

### 期間を限定する場合

`01_github_activity.bat`または`03_run_all.bat`の次の行

```bat
python "github_activity.py" --input "repositories.json" --ai
```

を，例えば次のように変更します．

```bat
python "github_activity.py" --input "repositories.json" --ai --since 2026-09-01 --until 2026-11-30
```

この設定はGitHub履歴取得側の期間指定です．既に取得したCSVのみから期間を絞りたい場合は，`02_summarize_github_class.bat`の集計コマンドに`--since`，`--until`を追加してください．
