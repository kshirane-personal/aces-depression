"""
研究で使用する変数定義・リコーディングルール・定数の一元管理
"""
from pathlib import Path

import numpy as np

# === パス定義 ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
OUTPUTS_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"

# === データファイル ===
MAIN_DATA = DATA_RAW / "LLCP2024.XPT "  # 末尾スペースあり（CDC原本のまま）
V1_DATA = DATA_RAW / "LLCP24V1.XPT"
V2_DATA = DATA_RAW / "LLCP24V2.XPT"

# === 分析用データセット（前処理の出力） ===
ANALYSIS_DATA = DATA_PROCESSED / "analysis_data.parquet"

# サンプルフロー（各段階での件数の記録）。学会発表でのサンプルサイズ説明と、
# 件数が想定外に減っていないかの検出に使う
SAMPLE_FLOW = DATA_INTERIM / "sample_flow.md"

# === レコード識別子 ===
# 3ソースは縦結合するため結合キーとしては使わない。個票の一意識別・重複チェック用
MERGE_KEYS = ["SEQNO", "_STATE"]

# === ウェイト変数 ===
# ソース別ウェイト。生データではソースごとに名前が異なる
WEIGHT_MAIN = "_LLCPWT"
WEIGHT_V1 = "_LCPWTV1"
WEIGHT_V2 = "_LCPWTV2"
WEIGHT_TRUNCATED = "_LLCPWT2"

# 統合後に使うウェイト。data_loader がソース別ウェイトをこの名前に統一する。
# 分析では常にこれを使う（CLAUDE.md「統計解析上の必須ルール」）
WEIGHT_FINAL = "_FINALWT"

# === サーベイデザイン変数 ===
# 生データから読み込む変数。_LLCPWT はメインデータにしか存在しない
SURVEY_VARS_SOURCE = ["_STATE", "SEQNO", "_STSTR", "_PSU", "_LLCPWT", "_LLCPWT2"]

# data_loader が統合時に作る派生変数
DERIVED_VARS = ["_SOURCE", WEIGHT_FINAL]

# 統合後のデータセットに実在するサーベイデザイン変数。
# _LLCPWT は3ソースの共通列に無いため統合時に落ちる。ウェイトは WEIGHT_FINAL を使う
SURVEY_VARS = ["_STATE", "SEQNO", "_STSTR", "_PSU", "_LLCPWT2"] + DERIVED_VARS

# === ACEモジュール実施州（FIPSコード） ===
ACE_STATES_MAIN = {12: "FL", 13: "GA", 15: "HI", 32: "NV", 38: "ND", 51: "VA", 72: "PR", 78: "USVI"}
ACE_STATES_V1 = {19: "IA", 23: "ME", 39: "OH"}
ACE_STATES_V2 = {4: "AZ", 40: "OK"}

# === アウトカム変数 ===
OUTCOME_PRIMARY = "ADDEPEV3"     # うつ病性障害の診断歴
OUTCOME_SECONDARY = "MENTHLTH"   # 過去30日間のメンタルヘルス不良日数

OUTCOME_VARS = [OUTCOME_PRIMARY, OUTCOME_SECONDARY]

# ADDEPEV3のリコーディング: 1=はい → 1, 2=いいえ → 0, 7/9=除外
ADDEPEV3_RECODE = {1.0: 1, 2.0: 0, 7.0: np.nan, 9.0: np.nan}

# MENTHLTH / PHYSHLTH の特殊値（88=0日, 77=わからない, 99=回答拒否）
MENTHLTH_RECODE = {88.0: 0, 77.0: np.nan, 99.0: np.nan}
PHYSHLTH_RECODE = {88.0: 0, 77.0: np.nan, 99.0: np.nan}

# === ACEs変数（13項目。うち11項目をACEスコアの8カテゴリに集約する） ===
# 家庭内の機能不全（はい/いいえ形式: 1=はい, 2=いいえ）
ACE_HOUSEHOLD = {
    "ACEDEPRS": "家庭内の精神疾患（うつ病・精神疾患・自殺傾向のある同居人）",
    "ACEDRINK": "家庭内の飲酒問題（問題飲酒者・アルコール依存症の同居人）",
    "ACEDRUGS": "家庭内の薬物使用（違法薬物使用・処方薬乱用の同居人）",
    "ACEPRISN": "家庭内の収監歴（刑務所に服役した同居人）",
    "ACEDIVRC": "親の離婚・別居",
}

# 虐待・DV（頻度形式: 1=Never, 2=Once, 3=More than once）
ACE_ABUSE_FREQ = {
    "ACEPUNCH": "DV目撃（親や同居の大人同士が互いに暴力をふるった頻度）",
    "ACEHURT1": "身体的虐待（親や同居の大人に殴る・蹴る等で身体的に傷つけられた頻度）",
    "ACESWEAR": "精神的虐待（罵倒・侮辱を受けた頻度）",
    "ACETOUCH": "性的虐待（性的接触を受けた頻度）",
    "ACETTHEM": "性的虐待（性的接触を試みられた頻度）",
    "ACEHVSEX": "性的虐待（性行為を強制された頻度）",
}

# ネグレクト（頻度形式: 1=Never〜5=All of the time、逆転項目）
ACE_NEGLECT = {
    "ACEADSAF": "情緒的安全（安全・守られていると感じた頻度、1=全くない〜5=いつも）",
    "ACEADNED": "基本的ニーズ（基本的な必要を満たそうとしてくれた頻度、1=全くない〜5=いつも）",
}

ACE_ALL_VARS = list(ACE_HOUSEHOLD.keys()) + list(ACE_ABUSE_FREQ.keys()) + list(ACE_NEGLECT.keys())

# ACEモジュール回答者の判定に使う設問（モジュール13の冒頭の設問）。
# 定義順に依存しないよう明示する。「ACE項目のいずれかに回答」に広げても
# 拾えるのは+1件のみだったため、単一設問での判定を採用している
ACE_FILTER_VAR = "ACEDEPRS"

# ACEスコア算出のための二値化ルール
# 家庭内の機能不全: 1(はい)→1, 2(いいえ)→0, 8(両親が未婚/ACEDIVRC用)→欠損
#
# 値8（両親が未婚）の扱いはCDCの2文書で見解が分かれる:
#   - MMWR 2023;72(26)   : 欠損として扱う（"responses of 'Parents not married' or
#                          'Don't know' were coded as missing"）
#   - CDC 2021年手順書    : Not Exposed(0) として扱う
# 本研究は主解析をMMWR 2023に合わせて「欠損」とする（実データで790件, 1.3%）。
# CDC 2021手順書に沿った版は感度分析として別途算出する（ACEDIVRC_RECODE_DIVRC8）。
ACE_HOUSEHOLD_RECODE = {1.0: 1, 2.0: 0, 7.0: np.nan, 8.0: np.nan, 9.0: np.nan}

# 感度分析用: ACEDIVRC の値8を Not Exposed(0) として扱う（CDC 2021年手順書準拠）
ACEDIVRC_RECODE_DIVRC8 = {1.0: 1, 2.0: 0, 7.0: np.nan, 8.0: 0, 9.0: np.nan}

# 虐待（頻度）: 1(Never/なし)→0, 2(Once/1回)→1, 3(More than once/2回以上)→1
ACE_ABUSE_FREQ_RECODE = {1.0: 0, 2.0: 1, 3.0: 1, 7.0: np.nan, 9.0: np.nan}

# ネグレクト（逆転項目）: 1(Never)/2(A little)/3(Some)→1（ネグレクト）, 4(Most)/5(All)→0（保護あり）
ACE_NEGLECT_RECODE = {1.0: 1, 2.0: 1, 3.0: 1, 4.0: 0, 5.0: 0, 7.0: np.nan, 9.0: np.nan}

# ACEスコアに使用する8カテゴリ（11項目を8カテゴリに集約）※主解析の曝露定義
ACE_CATEGORIES = {
    "ace_emotional_abuse": ["ACESWEAR"],          # 精神的虐待
    "ace_physical_abuse": ["ACEHURT1"],  # 身体的虐待（子どもが直接受けた暴力）
    "ace_sexual_abuse": ["ACETOUCH", "ACETTHEM", "ACEHVSEX"],  # 性的虐待（3項目のいずれか）
    "ace_household_mental": ["ACEDEPRS"],          # 家庭内の精神疾患
    "ace_household_substance": ["ACEDRINK", "ACEDRUGS"],  # 家庭内の物質依存（いずれか）
    "ace_household_dv": ["ACEPUNCH"],              # DV目撃（親同士の暴力）
    "ace_parental_separation": ["ACEDIVRC"],       # 親の離婚・別居
    "ace_household_incarceration": ["ACEPRISN"],   # 家族の収監
}

# ネグレクト2カテゴリ（感度分析用。主解析の ACE_CATEGORIES には含めない）
# 5段階頻度の逆転項目であり、二値化の閾値が他項目より恣意的なため主解析から外している。
# 例: ACEADSAF を 1-3=ネグレクトとすると該当12.6%、1-2なら6.9%、1のみなら4.3%と3倍動く。
# 一方でα（内的整合性）は 0.742→0.770 と改善し、追加で失うのは518件のみ。
# 両定義を事前指定し、フェーズ6で「ACEスコア定義」の感度分析として比較する。
ACE_CATEGORIES_NEGLECT = {
    "ace_neglect_emotional": ["ACEADSAF"],   # 情緒的ネグレクト（安全・被保護感）
    "ace_neglect_physical": ["ACEADNED"],    # 身体的ネグレクト（基本的ニーズ）
}

# 感度分析用の10カテゴリ（8カテゴリ + ネグレクト2カテゴリ）
ACE_CATEGORIES_EXTENDED = {**ACE_CATEGORIES, **ACE_CATEGORIES_NEGLECT}

# 感度分析用: 親の離婚カテゴリのみ ACEDIVRC=8→0 版に差し替えた8カテゴリ
# （カテゴリ数は主解析と同じ8。ACEDIVRC=8 の790件を欠損にせず拾う）
ACE_SCORE_COLS_DIVRC8 = [
    c for c in ACE_CATEGORIES if c != "ace_parental_separation"
] + ["ace_parental_separation_divrc8"]

# === 予防医療行動変数 ===
PREVENTIVE_CARE_VARS = {
    "CHECKUP1": "健康診断（最後の受診からの期間）",
    "FLUSHOT7": "インフルエンザ予防接種（過去12か月）",
    "LASTDEN4": "歯科受診（最後の受診からの期間）",
    "HIVTST7": "HIV検査（受検歴）",
    "HADMAM": "乳がん検診・マンモグラフィー（受検歴）",
    "CRVCLPAP": "子宮頸がん検診・Papテスト",
    "CRVCLHPV": "子宮頸がん検診・HPVテスト",
    "STOOLDN2": "大腸がん検診・便潜血検査",
    "PSATEST1": "前立腺がん検診・PSA検査",
}

# 予防医療行動の二値化（直近1年以内 → 1、それ以外 → 0）
CHECKUP1_RECODE = {1.0: 1, 2.0: 0, 3.0: 0, 4.0: 0, 7.0: np.nan, 8.0: 0, 9.0: np.nan}
LASTDEN4_RECODE = {1.0: 1, 2.0: 0, 3.0: 0, 4.0: 0, 7.0: np.nan, 8.0: 0, 9.0: np.nan}
FLUSHOT7_RECODE = {1.0: 1, 2.0: 0, 7.0: np.nan, 9.0: np.nan}
HIVTST7_RECODE = {1.0: 1, 2.0: 0, 7.0: np.nan, 9.0: np.nan}
HADMAM_RECODE = {1.0: 1, 2.0: 0, 7.0: np.nan, 9.0: np.nan}

# 予防医療行動リコーディングの一括定義（変数名→リコードマップ）
PREVENTIVE_CARE_RECODES = {
    "CHECKUP1": CHECKUP1_RECODE,
    "LASTDEN4": LASTDEN4_RECODE,
    "FLUSHOT7": FLUSHOT7_RECODE,
    "HIVTST7": HIVTST7_RECODE,
    "HADMAM": HADMAM_RECODE,
    "CRVCLPAP": {1.0: 1, 2.0: 0, 7.0: np.nan, 9.0: np.nan},
    "CRVCLHPV": {1.0: 1, 2.0: 0, 7.0: np.nan, 9.0: np.nan},
    "STOOLDN2": {1.0: 1, 2.0: 0, 7.0: np.nan, 9.0: np.nan},
    "PSATEST1": {1.0: 1, 2.0: 0, 7.0: np.nan, 9.0: np.nan},
}

# === 人口統計・SES変数 ===
DEMOGRAPHIC_VARS = {
    "_AGEG5YR": "年齢（5歳刻み14カテゴリ）",
    "_AGE_G": "年齢（6カテゴリ）",
    "_SEX": "性別（1=男性, 2=女性）",
    "_RACE": "人種/民族",
    "_RACEGR3": "人種/民族（5カテゴリ）",
    "MARITAL": "婚姻状況",
    "_EDUCAG": "教育水準（4カテゴリ）",
    "_INCOMG1": "世帯収入カテゴリ",
    "EMPLOY1": "雇用状態",
}

# === 医療アクセス変数 ===
HEALTH_ACCESS_VARS = {
    "_HLTHPL2": "健康保険加入（1=あり, 2=なし）",
    "MEDCOST1": "費用を理由に受診を控えた経験（過去12か月）",
    "PERSDOC3": "かかりつけ医の有無",
}

# === 健康行動・健康状態の共変量 ===
HEALTH_BEHAVIOR_VARS = {
    "_SMOKER3": "喫煙状況（4カテゴリ）",
    "_RFBING6": "過度飲酒（1=なし, 2=あり）",
    "_BMI5CAT": "BMIカテゴリ（4カテゴリ）",
    "_BMI5": "BMI（連続値×100）",
    "_TOTINDA": "運動習慣（1=あり, 2=なし）",
    "EXERANY2": "過去30日間の運動実施",
}

HEALTH_STATUS_VARS = {
    "GENHLTH": "主観的健康感（1=非常に良い〜5=悪い）",
    "PHYSHLTH": "過去30日間の身体的健康不良日数",
    "DIABETE4": "糖尿病の診断歴",
    "CVDINFR4": "心筋梗塞の診断歴",
    "CVDSTRK3": "脳卒中の診断歴",
    "_RFHLTH": "健康状態良好（1=良好, 2=不良）",
}

# === SDOH変数（オプショナル、実施州のみ） ===
SDOH_VARS = {
    "LSATISFY": "生活満足度（1=非常に満足〜4=非常に不満）",
    "SDLONELY": "孤独感の頻度",
    "SDHEMPLY": "過去12か月の失業・労働時間削減",
}

# === 全研究変数のリスト ===
ALL_RESEARCH_VARS = (
    OUTCOME_VARS
    + ACE_ALL_VARS
    + list(PREVENTIVE_CARE_VARS.keys())
    + list(DEMOGRAPHIC_VARS.keys())
    + list(HEALTH_ACCESS_VARS.keys())
    + list(HEALTH_BEHAVIOR_VARS.keys())
    + list(HEALTH_STATUS_VARS.keys())
    + list(SDOH_VARS.keys())
    + SURVEY_VARS_SOURCE
)

# === 共変量の定義 ===
# 共変量候補の母集合。フェーズ3のDAGで導出する「最小十分調整変数セット」とは別物
COVARIATE_VARS = (
    list(DEMOGRAPHIC_VARS.keys())
    + list(HEALTH_ACCESS_VARS.keys())
    + list(HEALTH_BEHAVIOR_VARS.keys())
    + list(HEALTH_STATUS_VARS.keys())
    + list(SDOH_VARS.keys())
)

# 共変量の欠損値コード（リコーディング対象外変数の「わからない/回答拒否」）
COVARIATE_MISSING_CODES = {
    "_AGEG5YR": [14.0],   # 13=80歳以上が最高齢カテゴリ。14はわからない/回答拒否/欠損
    "_RACE": [9.0],
    "_RACEGR3": [9.0],
    "MARITAL": [9.0],
    "_EDUCAG": [9.0],
    "_INCOMG1": [9.0],
    "EMPLOY1": [9.0],
    "_HLTHPL2": [9.0],
    "MEDCOST1": [7.0, 9.0],
    "PERSDOC3": [7.0, 9.0],
    "_SMOKER3": [9.0],
    "_RFBING6": [9.0],
    "_TOTINDA": [9.0],
    "EXERANY2": [7.0, 9.0],
    "GENHLTH": [7.0, 9.0],
    "DIABETE4": [7.0, 9.0],
    "CVDINFR4": [7.0, 9.0],
    "CVDSTRK3": [7.0, 9.0],
    "_RFHLTH": [9.0],
    "LSATISFY": [7.0, 9.0],
    "SDLONELY": [7.0, 9.0],
    "SDHEMPLY": [7.0, 9.0],
}

# 欠損値コードを持たない共変量（BLANK=NaNのみ）。登録漏れと区別するため明示する
COVARIATES_NO_MISSING_CODE = ["_SEX", "_AGE_G", "_BMI5CAT", "_BMI5"]

# 特殊値パターン（88=0日, 77/99=欠損）のため clean_covariates() で個別処理する共変量
COVARIATES_SPECIAL_HANDLING = ["PHYSHLTH"]

# === 欠損値処理の閾値 ===
MISSING_THRESHOLD_EXCLUDE = 0.30   # 30%以上欠損 → 変数除外
MISSING_THRESHOLD_IMPUTE = 0.05    # 5〜30%欠損 → 多重補完
# 5%未満 → 完全ケース分析

# === ACEスコアの層別化 ===
# 層別化は CDC MMWR 2023;72(26) 準拠の4群（zero / one / two to three / four or more）。
# 「4以上」の上限は None = 無制限。8カテゴリ(0-8)でも10カテゴリ(0-10)でも同じ定義で層別できる
ACE_SCORE_GROUPS = {
    "0": (0, 0),
    "1": (1, 1),
    "2-3": (2, 3),
    "4以上": (4, None),
}

# === 乱数シード ===
RANDOM_SEED = 42
