"""
synth_lib.py — 3트랙 종합(synthesis) 임팩트 분석 공용 라이브러리
================================================================

기존 산출물(seed TF-IDF ① · fastText 확장 ② · dense ③) 위에서만 동작한다.
재인코딩·재토큰화·무거운 임베딩·개별 트랙 재실행 없음 (가드레일).

핵심 규약 (세 트랙 공통, TF-IDF_기록.md §12.3 통일안):
  - 키: doc_id = "{stock_code(6자리 zfill)}_{fiscal_year}"  (회사명 merge 금지)
  - 표본: 127사 × 3년 = 381 기업-연도, 결측 0
  - GRADE_MAP = {S:6, A+:5, A:4, B+:3, B:2, C:1, D:0}  (이미 *_grade / esg_grade_num 에 반영)
  - z-score: 모집단 std (ddof=0)
  - 통일 통제 = {길이=log(II+IV+VI 문자수), 규모=log_assets} + 업종(기준 1차금속) + 연도(기준 2022)
  - 회귀: 순서형=OrderedModel(logit) · 이진=Logit · 연속=OLS, 모두 기업(stock_code) cluster SE
  - 인과 주장 금지 (연관/예측), p값과 효과크기 병기.
"""
from __future__ import annotations
import os, warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel
from scipy.stats import spearmanr, pearsonr

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------------- paths
ROOT = "/Users/home1/esg-dart-project"
DP   = f"{ROOT}/data/processed"
OZ   = f"{ROOT}/outputs/outputs_zip 압축해제한 폴더/data"   # dense Colab 산출물(번들)
FIG  = f"{ROOT}/reports/figures"
OUT_TBL = DP                                              # 07d_*.csv 저장 위치

TFIDF_FEAT = f"{DP}/05_tfidf_seed_features.parquet"
EXP_FEAT   = f"{DP}/05c_expanded_tfidf_features.parquet"
DENSE_TBL  = f"{OZ}/07_v2_analysis_table.csv"
SYNTH_TBL  = f"{DP}/07d_synthesis_table.csv"

# ----------------------------------------------------------------------------- column groups
GRADE_MAP = {"S": 6, "A+": 5, "A": 4, "B+": 3, "B": 2, "C": 1, "D": 0}

# 4 표현 family × E/S/G = 12 텍스트 점수. ("3트랙" = seed / 확장 / dense(cos·sup))
REPRS = {
    "seed_tfidf":  {"label": "① seed TF-IDF",   "track": 1, "cols": ["tfidf_E", "tfidf_S", "tfidf_G"]},
    "expanded":    {"label": "② fastText 확장",  "track": 2, "cols": ["expanded_tfidf_E", "expanded_tfidf_S", "expanded_tfidf_G"]},
    "dense_cos":   {"label": "③ dense cosine",   "track": 3, "cols": ["E_cos", "S_cos", "G_cos"]},
    "dense_sup":   {"label": "③ dense supervised", "track": 3, "cols": ["E_sup", "S_sup", "G_sup"]},
}
TEXT_COLS = [c for r in REPRS.values() for c in r["cols"]]            # 12개 raw
TEXT_COLS_Z = [c + "_z" for c in TEXT_COLS]

GRADE_COLS  = {"E": "e_grade", "S": "s_grade", "G": "g_grade"}        # 차원별 등급(수치)
INTEG_GRADE = "esg_grade_num"

SECTOR_DUMMIES = ["sector_IT·통신·미디어", "sector_금융·보험", "sector_기계·전자·운송장비",
                  "sector_유통·물류·건설·기타", "sector_음식료·소비재", "sector_제약·바이오·의료",
                  "sector_화학·소재"]                                  # 기준 = 1차금속
YEAR_DUMMIES = ["year_2023", "year_2024"]                            # 기준 = 2022
LEN_Z  = "log_core_doc_len_z"   # 길이 = log(II+IV+VI 문자수)
SIZE_Z = "log_assets_z"         # 규모 = log(자산)

# 통제 블록 (규모를 1차 교란으로 먼저 넣는 통일 순서, TF-IDF_기록.md §12.1·§12.3 근거)
CTRL_SIZE     = [SIZE_Z]
CTRL_LEN      = [LEN_Z]
CTRL_FULL     = [LEN_Z, SIZE_Z] + SECTOR_DUMMIES + YEAR_DUMMIES       # 완전통제

ALL_DIMS = ["E", "S", "G"]


# ----------------------------------------------------------------------------- font
def setup_font():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "AppleGothic"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 110
    plt.rcParams["savefig.bbox"] = "tight"
    return plt


# ----------------------------------------------------------------------------- z-score (ddof=0)
def zscore(s: pd.Series) -> pd.Series:
    s = s.astype(float)
    return (s - s.mean()) / s.std(ddof=0)


# ----------------------------------------------------------------------------- data load + 1:1 merge
def load_synthesis(rebuild: bool = False, save: bool = True) -> pd.DataFrame:
    """dense 기준 분석테이블(통제·등급·더미·z 포함)에 seed/확장 TF-IDF 텍스트 점수를 doc_id 1:1 병합."""
    if (not rebuild) and os.path.exists(SYNTH_TBL):
        return pd.read_csv(SYNTH_TBL, dtype={"stock_code_str": str})

    base = pd.read_csv(DENSE_TBL)                       # 381×37 (dense + 통제 + 등급 + 더미 + z)
    base["doc_id"] = base["doc_id"].astype(str)
    base["stock_code_str"] = base["stock_code"].astype(int).astype(str).str.zfill(6)

    t1 = pd.read_parquet(TFIDF_FEAT)
    t2 = pd.read_parquet(EXP_FEAT)
    for t in (t1, t2):
        t["doc_id"] = t["stock_code"].astype(str).str.zfill(6) + "_" + t["fiscal_year"].astype(int).astype(str)

    m = base.merge(t1[["doc_id", "tfidf_E", "tfidf_S", "tfidf_G"]], on="doc_id", how="left", validate="1:1")
    m = m.merge(t2[["doc_id", "expanded_tfidf_E", "expanded_tfidf_S", "expanded_tfidf_G"]],
                on="doc_id", how="left", validate="1:1")

    # 무결성 assert (가드레일)
    assert len(m) == 381, f"행수 {len(m)} != 381"
    miss = m[TEXT_COLS].isna().sum().sum()
    assert miss == 0, f"텍스트 점수 결측 {miss} (≠0) — 트랙 피처 동기화 필요"
    assert m["doc_id"].nunique() == 381, "doc_id 중복"

    # seed/확장 z-score 추가 (dense 점수는 base 에 이미 *_z 존재)
    for c in ["tfidf_E", "tfidf_S", "tfidf_G", "expanded_tfidf_E", "expanded_tfidf_S", "expanded_tfidf_G"]:
        m[c + "_z"] = zscore(m[c])

    if save:
        m.to_csv(SYNTH_TBL, index=False)
    return m


# ----------------------------------------------------------------------------- ordered logit (firm cluster SE)
def ll_null_ordered(y) -> float:
    """순서형 절편(threshold)만 있는 null 모형의 로그우도 = Σ_k n_k ln(n_k/n) (범주 주변빈도)."""
    vc = pd.Series(np.asarray(y)).value_counts()
    n = int(vc.sum())
    return float((vc * np.log(vc / n)).sum())


def fit_ordered(df: pd.DataFrame, ycol: str, xcols: list[str], group: str = "stock_code") -> dict:
    """OrderedModel(logit) + 기업 cluster SE. exog 계수만 추출 + McFadden pseudo-R²."""
    y = df[ycol].astype(int)
    yc = pd.Categorical(y, ordered=True)
    X = df[xcols].astype(float)
    mod = OrderedModel(yc, X, distr="logit")
    res = mod.fit(method="bfgs", maxiter=300, disp=False,
                  cov_type="cluster", cov_kwds={"groups": df[group].values})
    idx = list(xcols)
    ci = res.conf_int()
    lln = ll_null_ordered(y)
    return dict(
        res=res,
        params=res.params.reindex(idx),
        bse=res.bse.reindex(idx),
        pvals=res.pvalues.reindex(idx),
        ci_low=ci.reindex(idx).iloc[:, 0],
        ci_high=ci.reindex(idx).iloc[:, 1],
        llf=float(res.llf), aic=float(res.aic),
        mcfadden=float(1 - res.llf / lln), ll_null=lln,
        n=int(res.nobs), nclu=int(df[group].nunique()),
    )


def fit_ols(df: pd.DataFrame, ycol: str, xcols: list[str], group: str = "stock_code") -> dict:
    """OLS + 기업 cluster SE. R² 보고."""
    X = sm.add_constant(df[xcols].astype(float))
    res = sm.OLS(df[ycol].astype(float), X).fit(cov_type="cluster",
                                                 cov_kwds={"groups": df[group].values})
    return dict(res=res, r2=float(res.rsquared), r2_adj=float(res.rsquared_adj),
                params=res.params, bse=res.bse, pvals=res.pvalues, aic=float(res.aic),
                n=int(res.nobs), nclu=int(df[group].nunique()))


def fit_logit(df: pd.DataFrame, ycol: str, xcols: list[str], group: str = "stock_code") -> dict:
    """이진 Logit + 기업 cluster SE."""
    X = sm.add_constant(df[xcols].astype(float))
    res = sm.Logit(df[ycol].astype(int), X).fit(method="bfgs", maxiter=300, disp=False,
                                                 cov_type="cluster", cov_kwds={"groups": df[group].values})
    return dict(res=res, params=res.params, bse=res.bse, pvals=res.pvalues,
                prsquared=float(res.prsquared), aic=float(res.aic),
                n=int(res.nobs), nclu=int(df[group].nunique()))


def sig_stars(p: float) -> str:
    # 프로젝트 통일 표기: * p<.05, ** p<.01, *** p<.001 (p<.10 은 별 없음=경계/n.s.)
    if pd.isna(p):
        return ""
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""


# ----------------------------------------------------------------------------- partial correlation
def _resid(y: np.ndarray, Z: np.ndarray) -> np.ndarray:
    Zc = np.column_stack([np.ones(len(Z)), Z])
    beta, *_ = np.linalg.lstsq(Zc, y, rcond=None)
    return y - Zc @ beta


def partial_spearman(df: pd.DataFrame, xcol: str, ycol: str, ctrl_cols: list[str]) -> float:
    """부분 Spearman: 모든 변수를 순위변환 → 통제변수 잔차화(OLS) → 잔차 Pearson.
    (= rank 기반 부분상관. 통제 없으면 단순 Spearman.)"""
    if not ctrl_cols:
        return float(spearmanr(df[xcol], df[ycol]).statistic)
    rx = df[xcol].rank().to_numpy(float)
    ry = df[ycol].rank().to_numpy(float)
    Z = df[ctrl_cols].rank().to_numpy(float)
    ex, ey = _resid(rx, Z), _resid(ry, Z)
    return float(pearsonr(ex, ey)[0])


def partial_pearson(df: pd.DataFrame, xcol: str, ycol: str, ctrl_cols: list[str]) -> float:
    if not ctrl_cols:
        return float(pearsonr(df[xcol], df[ycol])[0])
    x = df[xcol].to_numpy(float); y = df[ycol].to_numpy(float)
    Z = df[ctrl_cols].to_numpy(float)
    return float(pearsonr(_resid(x, Z), _resid(y, Z))[0])


if __name__ == "__main__":
    m = load_synthesis(rebuild=True)
    print("synthesis table:", m.shape, "→", SYNTH_TBL)
    print("text cols present:", [c for c in TEXT_COLS if c in m.columns])
