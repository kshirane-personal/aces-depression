"""
データ前処理モジュール（フェーズ1）

リコーディング・ACEスコア算出・分析用データセットの出力を行う。
リコーディングルールは全て src/config.py から参照する。
"""
import warnings

import pandas as pd
import numpy as np

from src.config import (
    ADDEPEV3_RECODE, MENTHLTH_RECODE, PHYSHLTH_RECODE, MENT14D_RECODE,
    OUTCOME_ROBUSTNESS,
    ACE_HOUSEHOLD, ACE_ABUSE_FREQ, ACE_NEGLECT,
    ACE_HOUSEHOLD_RECODE, ACE_ABUSE_FREQ_RECODE, ACE_NEGLECT_RECODE,
    ACE_CATEGORIES, ACE_CATEGORIES_EXTENDED, ACE_SCORE_COLS_DIVRC8,
    ACEDIVRC_RECODE_DIVRC8, ACE_SCORE_GROUPS,
    PREVENTIVE_CARE_RECODES,
    COVARIATE_MISSING_CODES, PREVENTIVE_PRIMARY, PREVENTIVE_EXPLORATORY,
    ANALYSIS_DATA, SAMPLE_FLOW,
)
from src.data_loader import load_research_subset, get_load_flow


def recode_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """アウトカム変数のリコーディング"""
    # ADDEPEV3: 1→1(うつ病あり), 2→0(なし), 7/9→欠損
    if "ADDEPEV3" in df.columns:
        df["ADDEPEV3"] = df["ADDEPEV3"].map(ADDEPEV3_RECODE)

    # MENTHLTH: 88→0日, 77/99→欠損, 1-30はそのまま
    if "MENTHLTH" in df.columns:
        df["MENTHLTH"] = df["MENTHLTH"].replace(MENTHLTH_RECODE)
        mask = df["MENTHLTH"].notna() & ~df["MENTHLTH"].between(0, 30)
        df.loc[mask, "MENTHLTH"] = np.nan

    # _MENT14D: 9→欠損。値1-3（0日 / 1-13日 / 14日以上）はそのまま
    if OUTCOME_ROBUSTNESS in df.columns:
        df[OUTCOME_ROBUSTNESS] = df[OUTCOME_ROBUSTNESS].replace(MENT14D_RECODE)

    return df


def recode_ace_variables(df: pd.DataFrame) -> pd.DataFrame:
    """ACE変数のリコーディング（二値化）

    感度分析用に ACEDIVRC=8（両親が未婚）を Not Exposed(0) とした版の
    親の離婚カテゴリも作る。ACEDIVRC が上書きされる前に算出する必要がある。
    """
    if "ACEDIVRC" in df.columns:
        df["ace_parental_separation_divrc8"] = df["ACEDIVRC"].map(
            ACEDIVRC_RECODE_DIVRC8
        )

    for var in ACE_HOUSEHOLD:
        if var in df.columns:
            df[var] = df[var].map(ACE_HOUSEHOLD_RECODE)

    for var in ACE_ABUSE_FREQ:
        if var in df.columns:
            df[var] = df[var].map(ACE_ABUSE_FREQ_RECODE)

    for var in ACE_NEGLECT:
        if var in df.columns:
            df[var] = df[var].map(ACE_NEGLECT_RECODE)

    return df


def compute_ace_categories(
    df: pd.DataFrame, categories: dict | None = None
) -> pd.DataFrame:
    """ACEカテゴリの二値指標を算出

    各カテゴリに複数変数がある場合（例: 性的虐待 = ACETOUCH or ACETTHEM or ACEHVSEX、
    家庭内の物質依存 = ACEDRINK or ACEDRUGS）、いずれか1つでも該当→1、
    全て非該当→0、非該当と欠損の混在→欠損とする。
    カテゴリと変数の対応は config の定義が唯一の情報源。
    既定は感度分析用の10カテゴリを算出し、主解析のスコアは
    そのうち8カテゴリだけを合計して作る（compute_ace_score 参照）。
    """
    categories = ACE_CATEGORIES_EXTENDED if categories is None else categories
    for cat_name, variables in categories.items():
        available = [v for v in variables if v in df.columns]
        if not available:
            # 全欠損の列を作るとACEスコアが全員欠損になり、エラーなく完走して
            # 「有効 0件」とだけ出力される。静かな失敗を防ぐため中断する
            raise ValueError(
                f"ACEカテゴリ '{cat_name}' の構成変数 {variables} が"
                f"データに1つも存在しません。ACEスコアが全欠損になるため中断します。"
            )
        if len(available) < len(variables):
            # BRFSSは州・年次によって設問構成が変わる（MMWR 2023でも
            # Arkansasが性的虐待3問を1問に統合、New Hampshireが2問省略と報告）
            lacking = [v for v in variables if v not in df.columns]
            warnings.warn(
                f"ACEカテゴリ '{cat_name}' の構成変数 {lacking} が欠けています。"
                f"残る {available} のみで算出するため、他州・他年次との比較時は注意してください。",
                stacklevel=2,
            )

        if len(available) == 1:
            df[cat_name] = df[available[0]]
        else:
            cols = df[available]
            has_positive = (cols == 1).any(axis=1)
            all_zero = (cols == 0).all(axis=1)
            df[cat_name] = np.where(
                has_positive, 1.0,
                np.where(all_zero, 0.0, np.nan),
            )

    return df


def compute_ace_score(
    df: pd.DataFrame,
    cat_cols: list[str] | None = None,
    score_col: str = "ace_score",
    group_col: str = "ace_group",
) -> pd.DataFrame:
    """ACEスコアと層別グループを算出

    cat_cols は合計対象のカテゴリ列名リスト（既定は主解析の8カテゴリ）。
    全カテゴリのうち1つでも欠損があればスコアは欠損とする。
    これは CDC MMWR 2023 の完全ケース方式（"Participants with missing data for
    any type of ACE were excluded"）と同じ扱い。
    """
    cat_cols = list(ACE_CATEGORIES) if cat_cols is None else list(cat_cols)

    # min_count: 全カテゴリが有効でなければNaN
    df[score_col] = df[cat_cols].sum(axis=1, min_count=len(cat_cols))

    # 層別化（pd.cutで区間を定義）。上限Noneは無制限として扱うため、
    # カテゴリ数を増やしてもスコア上位がビンから外れてNaNになることはない
    groups = list(ACE_SCORE_GROUPS.items())
    bins = [groups[0][1][0] - 0.5]
    for _, (_, high) in groups:
        bins.append(np.inf if high is None else high + 0.5)
    labels = [label for label, _ in groups]

    df[group_col] = pd.cut(
        df[score_col], bins=bins, labels=labels, ordered=True,
    )

    return df


def recode_preventive_care(df: pd.DataFrame) -> pd.DataFrame:
    """予防医療行動変数のリコーディング（二値化）"""
    for var, recode_map in PREVENTIVE_CARE_RECODES.items():
        if var in df.columns:
            df[var] = df[var].map(recode_map)
    return df


def clean_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """共変量の欠損値コード処理

    PHYSHLTH は MENTHLTH と同じ特殊値パターン（88→0日, 77/99→欠損）。
    その他の共変量は COVARIATE_MISSING_CODES に定義された値を NaN に置換する。
    """
    if "PHYSHLTH" in df.columns:
        df["PHYSHLTH"] = df["PHYSHLTH"].replace(PHYSHLTH_RECODE)
        mask = df["PHYSHLTH"].notna() & ~df["PHYSHLTH"].between(0, 30)
        df.loc[mask, "PHYSHLTH"] = np.nan

    for var, codes in COVARIATE_MISSING_CODES.items():
        if var in df.columns:
            df[var] = df[var].replace({c: np.nan for c in codes})

    return df


def recode_all(df: pd.DataFrame) -> pd.DataFrame:
    """全リコーディングを適用し、ACEスコアを算出する

    ノートブックから呼び出す場合はこの関数を使う:
        from src.preprocess import recode_all
        df = recode_all(df)
    """
    df = df.copy()
    df = recode_outcomes(df)
    df = recode_ace_variables(df)
    df = compute_ace_categories(df, ACE_CATEGORIES_EXTENDED)
    # 主解析: 8カテゴリ（ace_score / ace_group）
    df = compute_ace_score(df, list(ACE_CATEGORIES), "ace_score", "ace_group")
    # 感度分析1: 10カテゴリ（ネグレクト2項目を追加）
    df = compute_ace_score(
        df, list(ACE_CATEGORIES_EXTENDED), "ace_score_ext", "ace_group_ext"
    )
    # 感度分析2: ACEDIVRC=8 を Not Exposed(0) として扱う（CDC 2021年手順書準拠）
    df = compute_ace_score(
        df, ACE_SCORE_COLS_DIVRC8, "ace_score_divrc8", "ace_group_divrc8"
    )
    df = recode_preventive_care(df)
    df = clean_covariates(df)
    return df


def write_sample_flow(df: pd.DataFrame) -> None:
    """各段階での件数を data/interim/sample_flow.md に書き出す

    学会発表でサンプルサイズを聞かれたときに即答できるようにするためと、
    件数が想定外に減っていないかを検出するための記録。
    """
    flow = get_load_flow()
    sources = ["MAIN", "V1", "V2"]
    stages = ["全レコード", "ACE実施州", "ACE回答者"]
    counts = {(s, st): n for s, st, n in flow}

    lines = [
        "# サンプルフロー",
        "",
        "`python -m src.preprocess` の実行時に自動生成。",
        "",
        "## 1. 読み込み（ソース別の絞り込み）",
        "",
        "V1 / V2 ファイルは MAIN の**部分集合**であり、回答者はMAINと重複する",
        "（オプショナルモジュールの回答を格納するための別ファイル）。",
        "本研究が各ファイルから抽出する州は互いに素なので、ACE回答者に重複はない。",
        "",
        "| ソース | ファイルのレコード数 | ACE実施州 | ACE回答者 |",
        "|---|---:|---:|---:|",
    ]
    totals = dict.fromkeys(stages, 0)
    for s in sources:
        vals = [counts.get((s, st), 0) for st in stages]
        for st, v in zip(stages, vals):
            totals[st] += v
        lines.append(f"| {s} | {vals[0]:,} | {vals[1]:,} | {vals[2]:,} |")
    t = [totals[st] for st in stages]
    lines.append(f"| **合計** | 重複のため計上せず | **{t[1]:,}** | **{t[2]:,}** |")

    universe = counts.get(("MAIN", "全レコード"), 0)
    if universe:
        lines += [
            "",
            f"BRFSS 2024 の総回答者 {universe:,}件 に対し、最終的な解析対象は "
            f"{t[2]:,}件（{t[2] / universe:.1%}）。",
        ]

    total = len(df)
    core_preventive = list(PREVENTIVE_PRIMARY) + list(PREVENTIVE_EXPLORATORY)
    lines += [
        "",
        f"## 2. 統合後（{total:,}件）の有効件数",
        "",
        "レコードを除外するのではなく、欠損の有無で使える件数が決まる。",
        "",
        "| 条件 | 件数 | 統合後に対する割合 |",
        "|---|---:|---:|",
    ]
    for label, mask in [
        ("うつ病診断歴（ADDEPEV3）が有効", df["ADDEPEV3"].notna()),
        ("ACEスコア（8カテゴリ）が有効", df["ace_score"].notna()),
        (
            f"主解析の予防医療2変数が有効（{' / '.join(PREVENTIVE_PRIMARY)}）",
            df[list(PREVENTIVE_PRIMARY)].notna().all(axis=1),
        ),
        (
            "**主解析の実効サンプル（ADDEPEV3・ACEスコア・主解析2変数すべて有効）**",
            df["ADDEPEV3"].notna()
            & df["ace_score"].notna()
            & df[list(PREVENTIVE_PRIMARY)].notna().all(axis=1),
        ),
        (
            "（参考）探索的記述を含む4変数すべて有効",
            df["ADDEPEV3"].notna()
            & df["ace_score"].notna()
            & df[core_preventive].notna().all(axis=1),
        ),
    ]:
        n = int(mask.sum())
        pct = f"{n / total:.1%}" if total else "-"
        lines.append(f"| {label} | {n:,} | {pct} |")
    lines += [
        "",
        "主解析の予防医療変数は config.PREVENTIVE_PRIMARY で事前指定（交互作用検定はこの2件のみ）。",
        "LASTDEN4 / HIVTST7 は探索的記述、がん検診系5変数は構造的欠損のため解析から除外。",
        "詳細は `docs/implementation_notes.md` を参照。",
        "",
    ]
    SAMPLE_FLOW.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_FLOW.write_text("\n".join(lines), encoding="utf-8")
    print(f"サンプルフロー: {SAMPLE_FLOW}")


def run_preprocessing() -> pd.DataFrame:
    """前処理パイプライン（データ読み込み→リコーディング→保存）"""
    print("データ読み込み中...")
    df = load_research_subset()

    print("リコーディング適用中...")
    df = recode_all(df)

    n = len(df)
    n_dep_valid = df["ADDEPEV3"].notna().sum()
    n_ace_valid = df["ace_score"].notna().sum()

    print(f"\n処理完了: {n:,}件")
    print(f"  ADDEPEV3 有効: {n_dep_valid:,} ({n_dep_valid / n:.1%})")
    if n_dep_valid > 0:
        dep_rate = df.loc[df["ADDEPEV3"].notna(), "ADDEPEV3"].mean()
        print(f"    うつ病あり: {(df['ADDEPEV3'] == 1).sum():,} ({dep_rate:.1%})")
    print(f"  ACEスコア 有効: {n_ace_valid:,} ({n_ace_valid / n:.1%})  ※主解析=8カテゴリ")
    if n_ace_valid > 0:
        print(f"    平均: {df['ace_score'].mean():.2f}, 中央値: {df['ace_score'].median():.0f}")
        for label in ACE_SCORE_GROUPS:
            count = (df["ace_group"] == label).sum()
            print(f"    {label}: {count:,} ({count / n_ace_valid:.1%})")

    for score_col, group_col, desc in [
        ("ace_score_ext", "ace_group_ext", "感度分析1: 10カテゴリ"),
        ("ace_score_divrc8", "ace_group_divrc8", "感度分析2: ACEDIVRC=8を0扱い"),
    ]:
        n_valid = df[score_col].notna().sum()
        print(f"  ACEスコア({desc}) 有効: {n_valid:,} ({n_valid / n:.1%})")
        if n_valid > 0:
            print(f"    平均: {df[score_col].mean():.2f}, 中央値: {df[score_col].median():.0f}")
            for label in ACE_SCORE_GROUPS:
                count = (df[group_col] == label).sum()
                print(f"    {label}: {count:,} ({count / n_valid:.1%})")

    df.to_parquet(ANALYSIS_DATA, index=False)
    print(f"\n保存先: {ANALYSIS_DATA}")
    write_sample_flow(df)

    return df


if __name__ == "__main__":
    run_preprocessing()
