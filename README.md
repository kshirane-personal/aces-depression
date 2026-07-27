# ACEs・予防医療行動・うつ病の交互作用研究（BRFSS 2024）

逆境的小児期体験（ACEs）と予防医療行動（ヘルスケア・エンゲージメント）の交互作用がうつ病リスクに及ぼす影響を、CDC BRFSS 2024データを用いて検証する。

## 研究概要

- **主目的**: 予防医療行動（健康診断・がん検診・歯科受診・予防接種）がACEsによるうつ病リスクの緩衝因子として機能するかを検証
- **副次目的**: 勾配ブースティング（XGBoost）とSHAP解析による非線形交互作用パターンの探索
- **データ**: BRFSS 2024（ACEモジュール実施13州/地域、約59,900件）

## 分析手法

- **確認的解析**: 交互作用項付きロジスティック回帰、RERI（加法的交互作用）、GAM
- **探索的解析**: XGBoost + SHAP交互作用値
- **因果推論枠組み**: DAGに基づく交絡調整

## プロジェクト構成

```
├── data/
│   ├── raw/          # BRFSS生データ（Git管理外 - data/raw/README.md参照）
│   ├── processed/    # 分析用データセット
│   └── interim/      # 中間ファイル
├── docs/             # 研究計画書・参考文献
├── notebooks/        # 探索的分析
├── src/              # 再利用可能な分析コード
├── outputs/
│   ├── figures/      # 図表
│   └── tables/       # 結果テーブル
└── requirements.txt  # Python依存パッケージ
```

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

BRFSS 2024データを[CDC](https://www.cdc.gov/brfss/annual_data/annual_2024.html)からダウンロードし、XPTファイルを`data/raw/`に配置する。

## プロジェクト管理

- **解析の全体設計・方針**: [`docs/analysis_workflow.md`](docs/analysis_workflow.md) — フェーズ構成、判断ポイント、完了条件を記載
- **個別のタスク・検証項目**: [GitHub Issues](../../issues) — 具体的なアクションを起票し、背景は workflow.md へリンク

## データソース

CDC Behavioral Risk Factor Surveillance System（BRFSS）2024年度。公開済み匿名化データ。
