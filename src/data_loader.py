"""
BRFSS 2024データの読み込み・統合ユーティリティ

メインデータ（LLCP2024）とオプショナルモジュール版（V1, V2）を統合し、
ACEモジュール回答者の研究用データセットを構築する。
"""
import pandas as pd
from src.config import (
    MAIN_DATA, V1_DATA, V2_DATA,
    WEIGHT_MAIN, WEIGHT_V1, WEIGHT_V2,
    ACE_ALL_VARS, ALL_RESEARCH_VARS,
    ACE_STATES_MAIN, ACE_STATES_V1, ACE_STATES_V2,
)


def load_xpt(path: str | object, columns: list[str] | None = None) -> pd.DataFrame:
    """XPTファイルを読み込み、指定列のみ返す"""
    df = pd.read_sas(str(path), format="xport")
    if columns:
        available = [c for c in columns if c in df.columns]
        df = df[available]
    return df


def load_main_ace_subset() -> pd.DataFrame:
    """メインデータからACEモジュール実施州のレコードを抽出"""
    df = load_xpt(MAIN_DATA)
    ace_states = set(ACE_STATES_MAIN.keys())
    mask = df["_STATE"].isin(ace_states) & df[ACE_ALL_VARS[0]].notna()
    df = df[mask].copy()
    df["_SOURCE"] = "MAIN"
    df["_FINALWT"] = df[WEIGHT_MAIN]
    return df


def load_v1_ace_subset() -> pd.DataFrame:
    """V1データからACEモジュール実施州のレコードを抽出"""
    df = load_xpt(V1_DATA)
    ace_states = set(ACE_STATES_V1.keys())
    mask = df["_STATE"].isin(ace_states) & df[ACE_ALL_VARS[0]].notna()
    df = df[mask].copy()
    df["_SOURCE"] = "V1"
    df["_FINALWT"] = df[WEIGHT_V1]
    return df


def load_v2_ace_subset() -> pd.DataFrame:
    """V2データからACEモジュール実施州のレコードを抽出"""
    df = load_xpt(V2_DATA)
    ace_states = set(ACE_STATES_V2.keys())
    mask = df["_STATE"].isin(ace_states) & df[ACE_ALL_VARS[0]].notna()
    df = df[mask].copy()
    df["_SOURCE"] = "V2"
    df["_FINALWT"] = df[WEIGHT_V2]
    return df


def load_merged_research_data(columns: list[str] | None = None) -> pd.DataFrame:
    """
    メイン・V1・V2を統合した研究用データセットを構築

    各ソースからACEモジュール回答者を抽出し、共通の列で縦結合する。
    ウェイト変数は _FINALWT に統一する。

    Parameters
    ----------
    columns : list[str] | None
        返す列を指定。Noneの場合はALL_RESEARCH_VARSを使用。

    Returns
    -------
    pd.DataFrame
        統合済みの研究用データセット
    """
    print("メインデータ読み込み中...", flush=True)
    df_main = load_main_ace_subset()
    print(f"  メイン: {len(df_main):,}件（{list(ACE_STATES_MAIN.values())}）")

    print("V1データ読み込み中...", flush=True)
    df_v1 = load_v1_ace_subset()
    print(f"  V1: {len(df_v1):,}件（{list(ACE_STATES_V1.values())}）")

    print("V2データ読み込み中...", flush=True)
    df_v2 = load_v2_ace_subset()
    print(f"  V2: {len(df_v2):,}件（{list(ACE_STATES_V2.values())}）")

    common_cols = sorted(
        set(df_main.columns) & set(df_v1.columns) & set(df_v2.columns)
    )
    extra_cols = ["_SOURCE", "_FINALWT"]
    use_cols = sorted(set(common_cols + extra_cols))

    df = pd.concat(
        [df_main[use_cols], df_v1[use_cols], df_v2[use_cols]],
        ignore_index=True,
    )
    print(f"統合完了: {len(df):,}件, {len(df.columns)}変数")

    if columns:
        available = [c for c in columns if c in df.columns]
        df = df[available]

    return df


def load_research_subset() -> pd.DataFrame:
    """研究関連変数のみに絞った軽量データセットを返す"""
    extra = ["_SOURCE", "_FINALWT"]
    cols = list(set(ALL_RESEARCH_VARS + extra))
    return load_merged_research_data(columns=cols)


if __name__ == "__main__":
    df = load_research_subset()
    print(f"\n最終データセット: {df.shape[0]:,}行 x {df.shape[1]}列")
    print(f"ソース別件数:\n{df['_SOURCE'].value_counts().to_string()}")
