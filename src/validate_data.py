"""
データ検証スクリプト

統合済みデータセットの整合性をチェックし、問題があれば警告を表示する。
"""
import pandas as pd
from src.config import (
    ACE_ALL_VARS,
    ACE_STATES_MAIN, ACE_STATES_V1, ACE_STATES_V2,
    MISSING_THRESHOLD_EXCLUDE, MISSING_THRESHOLD_IMPUTE,
    ALL_RESEARCH_VARS,
    COVARIATE_VARS, COVARIATE_MISSING_CODES,
    COVARIATES_NO_MISSING_CODE, COVARIATES_SPECIAL_HANDLING,
)
from src.data_loader import load_research_subset
from src.preprocess import recode_all


def check_covariate_coverage() -> None:
    """共変量の欠損値処理が漏れなく定義されているか確認

    共変量は「欠損値コードあり」「欠損値コードなし」「個別処理」のいずれかに
    必ず分類されている必要がある。未分類の変数は登録漏れの可能性が高い。
    データ読み込み前に実行できるため最初にチェックする。
    """
    print("=" * 60)
    print("0. 共変量の欠損値処理カバレッジ")
    print("=" * 60)
    classified = (
        set(COVARIATE_MISSING_CODES)
        | set(COVARIATES_NO_MISSING_CODE)
        | set(COVARIATES_SPECIAL_HANDLING)
    )
    print(f"  共変量: {len(COVARIATE_VARS)}変数")
    print(f"    欠損値コードあり: {len(COVARIATE_MISSING_CODES)}変数")
    print(f"    欠損値コードなし: {len(COVARIATES_NO_MISSING_CODE)}変数")
    print(f"    個別処理:         {len(COVARIATES_SPECIAL_HANDLING)}変数")

    unclassified = [v for v in COVARIATE_VARS if v not in classified]
    if unclassified:
        print(f"  [警告] 未分類の共変量（欠損値コードの登録漏れの可能性）: {unclassified}")
    else:
        print("  → 全ての共変量が分類済み")

    stale = sorted(v for v in classified if v not in COVARIATE_VARS)
    if stale:
        print(f"  [警告] 共変量グループに存在しない変数が登録されている: {stale}")


def check_record_counts(df: pd.DataFrame) -> None:
    """レコード数の確認"""
    print("=" * 60)
    print("1. レコード数")
    print("=" * 60)
    print(f"  総レコード数: {len(df):,}")
    print(f"  ソース別:")
    for src, count in df["_SOURCE"].value_counts().items():
        print(f"    {src}: {count:,}")


def check_state_distribution(df: pd.DataFrame) -> None:
    """ACEモジュール実施州の分布確認"""
    print("\n" + "=" * 60)
    print("2. 州別レコード数")
    print("=" * 60)
    all_ace_states = {**ACE_STATES_MAIN, **ACE_STATES_V1, **ACE_STATES_V2}
    state_counts = df["_STATE"].value_counts().sort_index()
    for fips, count in state_counts.items():
        name = all_ace_states.get(int(fips), f"不明({int(fips)})")
        print(f"  {name} (FIPS {int(fips)}): {count:,}")

    unexpected = set(df["_STATE"].dropna().astype(int)) - set(all_ace_states.keys())
    if unexpected:
        print(f"  [警告] 想定外の州コード: {unexpected}")


def check_missing_rates(df: pd.DataFrame, df_recoded: pd.DataFrame) -> None:
    """欠損率の確認と分類

    判定はリコード後（欠損値コード 7/9/77/99 等をNaN化した後）の欠損率で行う。
    生データの欠損率も併記し、欠損値コードがどれだけ寄与しているかを示す。
    """
    print("\n" + "=" * 60)
    print("3. 欠損率チェック（欠損値コード処理後で判定）")
    print("=" * 60)
    research_cols = [
        c for c in ALL_RESEARCH_VARS if c in df.columns and c in df_recoded.columns
    ]
    missing = df_recoded[research_cols].isnull().mean().sort_values(ascending=False)
    missing_raw = df[research_cols].isnull().mean()

    def show(var, rate):
        raw = missing_raw[var]
        note = f"（生データでは {raw:.1%}）" if abs(rate - raw) >= 0.001 else ""
        print(f"    {var}: {rate:.1%}{note}")

    high_missing = missing[missing >= MISSING_THRESHOLD_EXCLUDE]
    mid_missing = missing[
        (missing >= MISSING_THRESHOLD_IMPUTE) & (missing < MISSING_THRESHOLD_EXCLUDE)
    ]
    low_missing = missing[
        (missing > 0) & (missing < MISSING_THRESHOLD_IMPUTE)
    ]
    complete = missing[missing == 0]

    if len(high_missing) > 0:
        print(f"\n  [要除外] 欠損率30%以上（{len(high_missing)}変数）:")
        for var, rate in high_missing.items():
            show(var, rate)

    if len(mid_missing) > 0:
        print(f"\n  [要補完] 欠損率5-30%（{len(mid_missing)}変数）:")
        for var, rate in mid_missing.items():
            show(var, rate)

    if len(low_missing) > 0:
        print(f"\n  [完全ケース分析可] 欠損率5%未満（{len(low_missing)}変数）:")
        for var, rate in low_missing.items():
            show(var, rate)

    print(f"\n  [完全] 欠損なし: {len(complete)}変数")


def check_outcome_distribution(df: pd.DataFrame) -> None:
    """アウトカム変数の分布確認"""
    print("\n" + "=" * 60)
    print("4. アウトカム変数の分布")
    print("=" * 60)
    if "ADDEPEV3" in df.columns:
        print("\n  ADDEPEV3（うつ病診断歴）:")
        for val, count in df["ADDEPEV3"].value_counts(dropna=False).sort_index().items():
            pct = count / len(df) * 100
            label = {1.0: "はい", 2.0: "いいえ", 7.0: "わからない", 9.0: "回答拒否"}.get(
                val, f"欠損" if pd.isna(val) else f"値={val}"
            )
            print(f"    {label}: {count:,} ({pct:.1f}%)")

    if "MENTHLTH" in df.columns:
        valid = df["MENTHLTH"].dropna()
        valid_clean = valid[valid <= 30]
        print(f"\n  MENTHLTH（メンタルヘルス不良日数）:")
        print(f"    有効回答数: {len(valid_clean):,}")
        print(f"    平均: {valid_clean.mean():.1f}日, 中央値: {valid_clean.median():.0f}日")
        print(f"    0日: {(valid_clean == 0).sum():,} ({(valid_clean == 0).mean():.1%})")


def check_ace_distribution(df: pd.DataFrame) -> None:
    """ACE変数の分布確認"""
    print("\n" + "=" * 60)
    print("5. ACE変数の分布")
    print("=" * 60)
    for var in ACE_ALL_VARS:
        if var in df.columns:
            valid = df[var].dropna()
            print(f"  {var}: 有効={len(valid):,}, 分布={dict(valid.value_counts().sort_index())}")


def check_survey_weights(df: pd.DataFrame) -> None:
    """サーベイウェイトの確認"""
    print("\n" + "=" * 60)
    print("6. サーベイウェイト")
    print("=" * 60)
    if "_FINALWT" in df.columns:
        wt = df["_FINALWT"].dropna()
        print(f"  _FINALWT: 有効={len(wt):,}, 欠損={df['_FINALWT'].isna().sum()}")
        print(f"    最小={wt.min():.2f}, 最大={wt.max():.2f}")
        print(f"    平均={wt.mean():.2f}, 中央値={wt.median():.2f}")
        if (wt <= 0).any():
            print(f"  [警告] ウェイト0以下のレコード: {(wt <= 0).sum()}")


def run_all_checks() -> None:
    """全検証を実行"""
    check_covariate_coverage()

    print("\nデータ読み込み中...")
    df = load_research_subset()
    print("リコーディング適用中（欠損率判定用）...")
    df_recoded = recode_all(df)
    print()

    check_record_counts(df)
    check_state_distribution(df)
    check_missing_rates(df, df_recoded)
    check_outcome_distribution(df)
    check_ace_distribution(df)
    check_survey_weights(df)

    print("\n" + "=" * 60)
    print("検証完了")
    print("=" * 60)


if __name__ == "__main__":
    run_all_checks()
