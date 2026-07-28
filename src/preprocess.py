"""
データ前処理モジュール（フェーズ1）

リコーディング・ACEスコア算出・分析用データセットの出力を行う。
リコーディングルールは全て src/config.py から参照する。
"""
import pandas as pd
import numpy as np

pd.set_option("future.no_silent_downcasting", True)

from src.config import (
    ADDEPEV3_RECODE, MENTHLTH_RECODE, PHYSHLTH_RECODE,
    ACE_HOUSEHOLD, ACE_ABUSE_FREQ, ACE_NEGLECT,
    ACE_HOUSEHOLD_RECODE, ACE_ABUSE_FREQ_RECODE, ACE_NEGLECT_RECODE,
    ACE_CATEGORIES, ACE_SCORE_GROUPS,
    PREVENTIVE_CARE_RECODES,
    COVARIATE_MISSING_CODES,
    DATA_PROCESSED,
)
from src.data_loader import load_research_subset


def recode_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """アウトカム変数のリコーディング"""
    # ADDEPEV3: 1→1(うつ病あり), 2→0(なし), 7/9→欠損
    df["ADDEPEV3"] = df["ADDEPEV3"].map(ADDEPEV3_RECODE)

    # MENTHLTH: 88→0日, 77/99→欠損, 1-30はそのまま
    df["MENTHLTH"] = df["MENTHLTH"].replace(MENTHLTH_RECODE)
    mask = df["MENTHLTH"].notna() & ~df["MENTHLTH"].between(0, 30)
    df.loc[mask, "MENTHLTH"] = np.nan

    return df


def recode_ace_variables(df: pd.DataFrame) -> pd.DataFrame:
    """ACE変数のリコーディング（二値化）"""
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


def compute_ace_categories(df: pd.DataFrame) -> pd.DataFrame:
    """ACE 8カテゴリの二値指標を算出

    各カテゴリに複数変数がある場合（例: 身体的虐待 = ACEPUNCH or ACEHURT1）、
    いずれか1つでも該当→1、全て非該当→0、非該当と欠損の混在→欠損とする。
    """
    for cat_name, variables in ACE_CATEGORIES.items():
        available = [v for v in variables if v in df.columns]
        if not available:
            df[cat_name] = np.nan
            continue

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


def compute_ace_score(df: pd.DataFrame) -> pd.DataFrame:
    """ACEスコア（0-8）と層別グループを算出

    8カテゴリのうち1つでも欠損があればスコアは欠損とする（仮説ベース）。
    EDA後に部分欠損の許容範囲を再検討する可能性あり。
    """
    cat_cols = list(ACE_CATEGORIES.keys())

    # min_count=8: 8カテゴリ全て有効でなければNaN
    df["ace_score"] = df[cat_cols].sum(axis=1, min_count=len(cat_cols))

    # 層別化（pd.cutで区間を定義）
    groups = list(ACE_SCORE_GROUPS.items())
    bins = [groups[0][1][0] - 0.5]
    for _, (_, high) in groups:
        bins.append(high + 0.5)
    labels = [label for label, _ in groups]

    df["ace_group"] = pd.cut(
        df["ace_score"], bins=bins, labels=labels, ordered=True,
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
    df = compute_ace_categories(df)
    df = compute_ace_score(df)
    df = recode_preventive_care(df)
    df = clean_covariates(df)
    return df


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
    print(f"  ACEスコア 有効: {n_ace_valid:,} ({n_ace_valid / n:.1%})")
    if n_ace_valid > 0:
        print(f"    平均: {df['ace_score'].mean():.2f}, 中央値: {df['ace_score'].median():.0f}")
        for label in ACE_SCORE_GROUPS:
            count = (df["ace_group"] == label).sum()
            print(f"    {label}: {count:,} ({count / n_ace_valid:.1%})")

    output_path = DATA_PROCESSED / "analysis_data.parquet"
    df.to_parquet(output_path, index=False)
    print(f"\n保存先: {output_path}")

    return df


if __name__ == "__main__":
    run_preprocessing()
