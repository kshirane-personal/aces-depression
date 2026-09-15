# ACEs-うつ病交互作用研究（BRFSS 2024）

逆境的小児期体験（ACEs）と予防医療行動（ヘルスケア・エンゲージメント）の交互作用がうつ病リスクに及ぼす影響を、CDC BRFSS 2024データで検証する研究プロジェクト。

- 主仮説: ACEスコアが高い集団で、予防医療行動への参加がうつ病有病率の低さと関連する
- 確認的解析（ロジスティック回帰・RERI）と探索的解析（XGBoost・SHAP）の二層構造

## リファレンス

@docs/data_dictionary.md
@docs/analysis_workflow.md

研究計画の全体構想は `docs/research_plan.docx`（`pandoc -t markdown` で読める）。

## 環境セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

生データ（XPTファイル）は CDC からダウンロードし `data/raw/` に手動配置する（Git管理外）。

## データパイプライン


| モジュール                  | 役割                             | 実行方法                          |
| ---------------------- | ------------------------------ | ----------------------------- |
| `src/config.py`        | 変数定義・リコーディングルール・定数の**唯一の情報源**  | import して使用                   |
| `src/data_loader.py`   | BRFSS 3ソース（MAIN/V1/V2）の読み込みと統合 | `python -m src.data_loader`   |
| `src/validate_data.py` | 統合データの整合性チェック                  | `python -m src.validate_data` |
| `src/run_all.py`       | 全パイプラインのマスタースクリプト              | `python -m src.run_all`       |


新しい分析モジュールは `src/` に配置し、`run_all.py` のステップとして組み込む。

## 言語ルール

- コメント・docstring・print出力・ドキュメント: **日本語**
- 変数名・関数名: **英語**（Pythonの慣例に従う）
- 論文化の段階で英語に変換する。それまでは日本語優先



## コーディング規約

- 変数定義の追加・変更は必ず `src/config.py` に集約する。分析コードにマジックナンバーや変数名のハードコーディングをしない
- 乱数シード: `config.RANDOM_SEED`（42）を一貫して使用
- 図表の出力先: `outputs/figures/`、`outputs/tables/`
- データの中間出力: `data/interim/`、分析用データセット: `data/processed/`



## 統計解析上の必須ルール

- サーベイウェイト `_FINALWT` を**常に**適用する。重みなし分析は感度分析としてのみ実施
- 標準誤差の推定にはサーベイデザイン変数（`_STSTR`, `_PSU`）を使用する
- 交差検証は `GroupKFold`（州 `_STATE` をグルーピング変数、5分割）を使用し、同一州のデータが訓練・テストに分割されることを防ぐ
- 欠損値コード 7, 9, 77, 99 は「わからない/回答拒否」であり、分析上は欠損（NaN）として扱う
- ACEスコアの算出は CDC MMWR 2023;72(26) に準拠する（8カテゴリ、完全ケース、層別は 0 / 1 / 2-3 / 4以上 の4群）。定義の根拠と出典は `docs/data_dictionary.md` の「ACEスコアの算出方法」に記載
- 主解析は必ず8カテゴリ版（`ace_score` / `ace_group`）を使う。感度分析用の `ace_score_ext`（10カテゴリ）と `ace_score_divrc8`（ACEDIVRC=8を0扱い）はフェーズ6専用で、主解析に使わない
- 欠損率の閾値: 30%以上→変数除外、5-30%→多重補完（MICE）、5%未満→完全ケース分析



## ゴッチャ・注意点

- `LLCP2024.XPT` のファイル名にCDC原本由来の**末尾スペース**がある。`config.MAIN_DATA` で対応済みなので、パスは必ず config 経由で参照する
- BRFSSは複合サンプリングデザインを採用している。`df.mean()` 等の単純な集計は母集団を代表しない。必ずサーベイウェイトを適用する
- SDOH変数（LSATISFY, SDLONELY, SDHEMPLY）はオプショナルモジュールのため高欠損率が予想される。主解析ではなくサブ解析に位置づける可能性がある
- ACEモジュールは13州・地域でのみ実施されており、全米代表のデータではない
- 主アウトカム `ADDEPEV3` は生涯診断歴（「医師にうつ病と言われたことがあるか」）であり、現在のうつ状態を測定していない。結果の解釈で明示する
- 本研究は横断データに基づくため、因果関係は主張できない。「関連」「交互作用」として記述する
- 性別限定変数: `HADMAM`（女性）、`PSATEST1`（男性）は複合指標構成時に除外し個別分析に回す
- ACE変数の `ACEPUNCH` は「親や同居の大人**同士**が互いに暴力をふるった頻度」であり、DV目撃カテゴリにのみ使用する。子ども自身が受けた暴力（身体的虐待）は `ACEHURT1`。両者を混同しない（`config.ACE_CATEGORIES` 参照）



## タスク管理の棲み分け

- **`docs/analysis_workflow.md`** = フェーズの全体地図。方針レベルの判断（仮説ベース項目、更新トリガー、完了条件）を管理する。情報の正はここ
- **GitHub Issues** = 具体的なネクストアクションや小さな検証タスク。背景の説明は workflow.md へのリンク（例: `docs/analysis_workflow.md のフェーズ1-3参照`）で済ませ、Issue 側に方針の文言をコピペしない



## Git管理のルール

- `data/raw/` のXPTファイルはGit管理外（`.gitignore` 済み）
- `data/processed/`、`outputs/` の中身もGit管理外（コードから再生成可能）
- `_confidential`、`_internal` サフィックスのファイルは絶対にコミットしない

