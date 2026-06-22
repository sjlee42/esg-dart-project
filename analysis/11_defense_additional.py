"""Defense-only additional analyses.

Outputs:
- data/processed/11_defense_*.csv
- outputs/11_defense_summary.md
- notebooks/11_논문방어_추가분석.ipynb

The code reuses analysis/synth_lib.py so controls, z-scores, and cluster-SE
conventions stay aligned with the submitted analysis.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import nbformat as nbf
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path("/Users/home1/esg-dart-project")
sys.path.insert(0, str(ROOT / "analysis"))

import synth_lib as S  # noqa: E402

DP = ROOT / "data/processed"
OUT = ROOT / "outputs"
NB = ROOT / "notebooks/11_논문방어_추가분석.ipynb"


GROUPS = {
    "규모": [S.SIZE_Z],
    "분량": [S.LEN_Z],
    "업종": S.SECTOR_DUMMIES,
    "연도": S.YEAR_DUMMIES,
}


def nonconstant_cols(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c in df.columns and df[c].nunique(dropna=False) > 1]


def p_adjust(pvals: pd.Series) -> pd.DataFrame:
    p = pvals.astype(float).to_numpy()
    n = len(p)
    bonf = np.minimum(p * n, 1.0)
    order = np.argsort(p)
    ranked = p[order]
    bh_sorted = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        val = ranked[i] * n / (i + 1)
        prev = min(prev, val)
        bh_sorted[i] = prev
    bh = np.empty(n, dtype=float)
    bh[order] = np.minimum(bh_sorted, 1.0)
    return pd.DataFrame({"p_raw": p, "p_bonferroni": bonf, "p_bh_fdr": bh})


def exact_lmg(df: pd.DataFrame, y: str, groups: dict[str, list[str]]) -> pd.DataFrame:
    """Exact group-level LMG/Shapley by averaging marginal R2 over all 4! orders."""
    cache_ols: dict[tuple[str, ...], float] = {tuple(): 0.0}
    cache_mcf: dict[tuple[str, ...], float] = {tuple(): 0.0}

    def cols_for(keys: tuple[str, ...]) -> list[str]:
        cols: list[str] = []
        for k in keys:
            cols.extend(groups[k])
        return cols

    def r2_for(keys: tuple[str, ...], kind: str) -> float:
        keys = tuple(keys)
        cache = cache_ols if kind == "ols" else cache_mcf
        if keys not in cache:
            cols = cols_for(keys)
            if kind == "ols":
                cache[keys] = S.fit_ols(df, y, cols)["r2"]
            else:
                cache[keys] = S.fit_ordered(df, y, cols)["mcfadden"]
        return cache[keys]

    rows = []
    keys = list(groups)
    for order in itertools.permutations(keys):
        prev: tuple[str, ...] = tuple()
        for k in order:
            cur = prev + (k,)
            rows.append({
                "order": " > ".join(order),
                "variable": k,
                "ols_marginal": r2_for(cur, "ols") - r2_for(prev, "ols"),
                "mcf_marginal": r2_for(cur, "mcf") - r2_for(prev, "mcf"),
            })
            prev = cur
    contrib = pd.DataFrame(rows).groupby("variable", as_index=False).agg(
        ols_lmg=("ols_marginal", "mean"),
        mcf_lmg=("mcf_marginal", "mean"),
        ols_min=("ols_marginal", "min"),
        ols_max=("ols_marginal", "max"),
        mcf_min=("mcf_marginal", "min"),
        mcf_max=("mcf_marginal", "max"),
    )
    contrib["ols_share"] = contrib["ols_lmg"] / contrib["ols_lmg"].sum()
    contrib["mcf_share"] = contrib["mcf_lmg"] / contrib["mcf_lmg"].sum()
    return contrib.sort_values("ols_lmg", ascending=False)


def hierarchical(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    prev_ols = prev_mcf = 0.0
    order = ["규모", "분량", "업종", "연도"]
    cols: list[str] = []
    for name in order:
        cols += GROUPS[name]
        use_cols = nonconstant_cols(df, cols)
        ols = S.fit_ols(df, S.INTEG_GRADE, use_cols)["r2"]
        mcf = S.fit_ordered(df, S.INTEG_GRADE, use_cols)["mcfadden"]
        rows.append({
            "block": "+" + name,
            "ols_r2": ols,
            "ols_dr2": ols - prev_ols,
            "mcfadden": mcf,
            "mcf_dr2": mcf - prev_mcf,
        })
        prev_ols, prev_mcf = ols, mcf
    return pd.DataFrame(rows)


def fullcontrol_coef(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for repr_key, meta in S.REPRS.items():
        for dim, col in zip(S.ALL_DIMS, meta["cols"]):
            z = col + "_z"
            if z not in df.columns:
                df = df.assign(**{z: S.zscore(df[col])})
            xcols = nonconstant_cols(df, [z] + S.CTRL_FULL)
            res = S.fit_ordered(df, S.GRADE_COLS[dim], xcols)
            p = float(res["pvals"][z])
            rows.append({
                "repr": repr_key,
                "label": meta["label"],
                "dim": dim,
                "score": col,
                "target": S.GRADE_COLS[dim],
                "coef": float(res["params"][z]),
                "p": p,
                "ci_low": float(res["ci_low"][z]),
                "ci_high": float(res["ci_high"][z]),
                "sig": S.sig_stars(p),
                "n": res["n"],
                "n_clusters": res["nclu"],
            })
    return pd.DataFrame(rows)


def text_size_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    targets = [("log_assets", "log(total_assets)"), ("log_core_doc_len", "log(document_length)")]
    for score in S.TEXT_COLS:
        for col, label in targets:
            r = spearmanr(df[score], df[col])
            rows.append({
                "score": score,
                "target": label,
                "rho": float(r.statistic),
                "p": float(r.pvalue),
            })
    return pd.DataFrame(rows)


def dimension_size_r2(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim, y in S.GRADE_COLS.items():
        ols = S.fit_ols(df, y, [S.SIZE_Z])
        ord_ = S.fit_ordered(df, y, [S.SIZE_Z])
        rows.append({
            "dimension": dim,
            "target": y,
            "ols_r2": ols["r2"],
            "ols_p_size": float(ols["pvals"][S.SIZE_Z]),
            "mcfadden": ord_["mcfadden"],
            "ordered_p_size": float(ord_["pvals"][S.SIZE_Z]),
            "ordered_coef_size": float(ord_["params"][S.SIZE_Z]),
        })
    return pd.DataFrame(rows)


def industry_distribution(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    return (
        df.groupby("sector", as_index=False)
        .agg(company_years=("doc_id", "size"), companies=("stock_code", "nunique"))
        .assign(ratio=lambda x: x["company_years"] / n)
        .sort_values(["company_years", "sector"], ascending=[False, True])
    )


def number_density_optional(df: pd.DataFrame) -> pd.DataFrame:
    pre = pd.read_csv(DP / "dart_preprocessed.csv")
    keys = pd.read_parquet(DP / "05_tfidf_seed_features.parquet")[["company_name", "stock_code", "fiscal_year", "esg_year"]]
    pre = pre.rename(columns={"회사이름": "company_name"}).merge(
        keys, on=["company_name", "esg_year"], how="left", validate="1:1"
    )
    pre["doc_id"] = pre["stock_code"].astype(str).str.zfill(6) + "_" + pre["fiscal_year"].astype(int).astype(str)
    pat = r"\d|%|억원|조원|tCO2e|MWh|kWh|톤|천원|백만원"
    pre["numeric_hits"] = pre["raw_text"].fillna("").str.count(pat)
    pre["numeric_density_per_1k_char"] = pre["numeric_hits"] / pre["raw_text"].fillna("").str.len().replace(0, np.nan) * 1000
    out = df[["doc_id", "log_assets", "esg_grade_num", "e_grade", "s_grade", "g_grade"]].merge(
        pre[["doc_id", "numeric_hits", "numeric_density_per_1k_char"]], on="doc_id", how="left", validate="1:1"
    )
    return out


def summarize(m: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> str:
    controls = pd.read_csv(DP / "company_controls.csv")
    cfs = controls["assets_fs_div"].value_counts(dropna=False).to_dict()
    original_a1 = pd.read_csv(DP / "07d_a1_hierarchical_r2.csv")
    fc = tables["table5_adjusted"]
    surv_bh = fc[fc["p_bh_fdr"] < 0.05][["label", "dim", "coef", "p_raw", "p_bh_fdr"]]
    nofin = tables["finance_excluded_fullcontrol"]
    orig = pd.read_csv(DP / "07d_a3_fullcontrol_coef.csv")
    compare = orig.merge(nofin, on=["repr", "dim"], suffixes=("_orig", "_nofin"))
    seed_g = compare[(compare["repr"] == "seed_tfidf") & (compare["dim"] == "G")].iloc[0]
    sup_s = compare[(compare["repr"] == "dense_sup") & (compare["dim"] == "S")].iloc[0]
    lmg = tables["lmg_shapley"]
    size_lmg = lmg[lmg["variable"] == "규모"].iloc[0]
    dim = tables["dimension_size_r2"]
    ind = tables["industry_distribution"].head(3)
    corr = tables["text_size_corr"]

    lines = []
    lines.append("# 논문 방어용 추가 분석 요약\n")
    lines.append("## A-1. LMG/Shapley 상대기여도 분석")
    lines.append(f"- 발견 여부: 새로 계산 완료. 규모 LMG OLS={size_lmg.ols_lmg:.3f}, share={size_lmg.ols_share:.1%}; McFadden={size_lmg.mcf_lmg:.3f}, share={size_lmg.mcf_share:.1%}.")
    lines.append(f"- 관련 파일: `data/processed/11_defense_lmg_shapley.csv`, 기존 순차투입 `data/processed/07d_a1_hierarchical_r2.csv`.")
    lines.append(f"- 핵심 수치: 기존 순차투입 규모 ΔR²={original_a1.iloc[0]['ols_dr2']:.3f}; LMG 순위는 " + ", ".join(f"{r.variable} {r.ols_lmg:.3f}" for r in lmg.itertuples()) + ".")
    lines.append("- 논문 반영 위치: 5-1 규모 설명력 순서 의존성 검증. 규모가 여전히 최대 기여.")
    lines.append("\n## A-2. 다중검정 보정")
    lines.append(f"- 발견 여부: Table 5 후보 12개 자기차원 완전통제 p-value 보정 완료.")
    lines.append("- 관련 파일: `data/processed/11_defense_table5_p_adjusted.csv`, 원본 `data/processed/07d_a3_fullcontrol_coef.csv`.")
    lines.append("- 핵심 수치: BH-FDR 생존 신호: " + (", ".join(f"{r.label}-{r.dim} β={r.coef:.3f}, q={r.p_bh_fdr:.3f}" for r in surv_bh.itertuples()) or "없음") + ".")
    lines.append("- 논문 반영 위치: 5-2 Table 5 다중검정 보정 주석/부록.")
    lines.append("\n## A-3. 텍스트 점수 × 규모 상관표")
    lines.append(f"- 발견 여부: 12×2 Spearman 계산 완료. log_assets와 절대상관 최대={corr[corr.target=='log(total_assets)'].rho.abs().max():.3f}, log_length와 절대상관 최대={corr[corr.target=='log(document_length)'].rho.abs().max():.3f}.")
    lines.append("- 관련 파일: `data/processed/11_defense_text_size_correlations.csv`.")
    lines.append("- 핵심 수치: 상세 rho/p는 CSV 참조.")
    lines.append("- 논문 반영 위치: 6-2 규모 편향 근거 표.")
    lines.append("\n## A-4. 금융업 제외 강건성")
    lines.append(f"- 발견 여부: 금융·보험 제외 후 재추정 완료. 표본 {len(m)}→{len(m[m['sector']!='금융·보험'])}.")
    lines.append("- 관련 파일: `data/processed/11_defense_finance_excluded_hierarchical_r2.csv`, `data/processed/11_defense_finance_excluded_fullcontrol.csv`.")
    lines.append(f"- 핵심 수치: 규모 ΔR² {original_a1.iloc[0]['ols_dr2']:.3f}→{tables['finance_excluded_hierarchical'].iloc[0]['ols_dr2']:.3f}; seed-G β {seed_g.coef_orig:.3f}(p={seed_g.p_orig:.3g})→{seed_g.coef_nofin:.3f}(p={seed_g.p_nofin:.3g}); supervised-S β {sup_s.coef_orig:.3f}(p={sup_s.p_orig:.3g})→{sup_s.coef_nofin:.3f}(p={sup_s.p_nofin:.3g}).")
    lines.append("- 논문 반영 위치: 3-4 금융업 제외 강건성.")
    lines.append("\n## A-5. 차원별 규모 설명력")
    lines.append("- 발견 여부: E/S/G 각각 `등급 ~ log_assets` 계산 완료.")
    lines.append("- 관련 파일: `data/processed/11_defense_dimension_size_r2.csv`.")
    lines.append("- 핵심 수치: " + "; ".join(f"{r.dimension}: R²={r.ols_r2:.3f}, p={r.ols_p_size:.2g}, pseudo-R²={r.mcfadden:.3f}" for r in dim.itertuples()) + ".")
    lines.append("- 논문 반영 위치: 4-6 G만 규모를 반영하는지 확인. 결과는 G만이 아니라 E/S/G 모두 규모 영향.")
    lines.append("\n## B-1. 총자산 변수 확인")
    lines.append(f"- 발견 여부: 확인 완료. `assets_fs_div` 분포={cfs}.")
    lines.append("- 관련 파일: `data/processed/company_controls.csv`, `analysis/synth_lib.py`.")
    lines.append("- 핵심 수치: 최종 `log_assets`는 `assets`의 로그. 기준은 CFS(연결) 우선이며 CFS 345건 + CFS_MANUAL 18건, OFS fallback 18건이 포함됨.")
    lines.append("- 논문 반영 위치: 자료/변수 정의.")
    lines.append("\n## B-2. '아홉 가지 점수' 확인")
    lines.append("- 발견 여부: 확인 완료. 9개는 비지도 점수(seed TF-IDF 3 + fastText 확장 3 + dense cosine 3). 최종 종합표에는 dense supervised 3개를 더해 12개도 보유.")
    lines.append("- 관련 파일: `analysis/synth_lib.py`, `analysis/_build_notebook.py`.")
    lines.append("- 핵심 수치: 포함 9개=`tfidf_*`, `expanded_tfidf_*`, `E/S/G_cos`; 제외/별도=`E/S/G_sup`(등급을 학습한 상한/검증 점수).")
    lines.append("- 논문 반영 위치: 측정치 구성 설명.")
    lines.append("\n## B-3. KCGS 등급 연도 매칭 확인")
    lines.append("- 발견 여부: 확인 완료.")
    lines.append("- 관련 파일: `notebooks/보고용_분석노트북.ipynb`, `plan/04_preprocessing.md`, `analysis/synth_lib.py`.")
    lines.append("- 핵심 수치: `doc_id={stock_code}_{fiscal_year}`, `esg_year=fiscal_year+1`; join key는 회사명 단독이 아니라 `company_name + esg_year` 및 최종 `doc_id`.")
    lines.append("- 논문 반영 위치: 데이터 매칭/식별 전략.")
    lines.append("\n## B-4. KCGS 평가체계 개정 여부")
    lines.append("- 발견 여부: 내부 자료에서는 분석기간 중 평가체계 개정 사실을 직접 입증하는 파일을 발견하지 못함.")
    lines.append("- 관련 파일: `협업가이드자료/KCGS_ESG_평가방법론_정리.md`, `조언.md`.")
    lines.append("- 핵심 수치: 내부 근거만으로 '변경 없음'이라고 단정 불가. 논문에는 '내부 자료 기준 확인 불가/한계'로 표기 권장.")
    lines.append("- 논문 반영 위치: 한계/자료 설명.")
    lines.append("\n## B-5. 업종 분포")
    lines.append("- 발견 여부: 계산 완료.")
    lines.append("- 관련 파일: `data/processed/11_defense_industry_distribution.csv`.")
    lines.append("- 핵심 수치: 상위 업종 " + "; ".join(f"{r.sector}: {r.company_years}건({r.ratio:.1%}), {r.companies}사" for r in ind.itertuples()) + ".")
    lines.append("- 논문 반영 위치: 표본 설명.")
    lines.append("\n## C/D. 기타 확인")
    lines.append("- C-1 max_df=1.0: 기존 문서에서 seed-G 0.38→0.51 강건성 언급 발견(`analysis/_build_notebook.py`, `outputs/발표자료_v2.md`).")
    lines.append("- C-2 앵커/ABTT/whitening: dense 개선 기록 발견(`plan/01_rationale.md`, `notebooks/07b_dense_esg_v2_colab.ipynb`).")
    lines.append("- C-3 OOF 검증: GroupKFold 기업 단위 OOF 및 누설 방지 기록 발견(`outputs/final_report_detailed.html`, `notebooks/07b_dense_esg_v2_colab.ipynb`).")
    lines.append("- C-4 사례분석: DRIVER/BOILER, 상하위 10, Mann-Whitney, 밀도 상관 산출물 발견(`data/processed/08_h2_*.csv`).")
    lines.append("- D-1 숫자 밀도: 선택 분석으로 계산 완료(`data/processed/11_defense_number_density.csv`, `data/processed/11_defense_number_density_correlations.csv`).")
    lines.append("- D-2/D-3: 이번 실행에서는 시간상 신규 계산하지 않음. D-3은 기존 `data/processed/08_h4_length_sensitivity.csv`와 `07d_a4_length_myth.csv`에 문장 수/문자 수 민감도 일부 존재.")
    return "\n".join(lines) + "\n"


def build_notebook() -> None:
    nb = nbf.v4.new_notebook()
    cells = []
    md = lambda text: cells.append(nbf.v4.new_markdown_cell(text))
    code = lambda text: cells.append(nbf.v4.new_code_cell(text))

    md("# 논문 방어용 추가 분석\n\n기존 산출물 위에서만 계산합니다. 통제변수와 모형은 `analysis/synth_lib.py`를 재사용합니다.")
    code("import sys, runpy\nfrom pathlib import Path\nimport numpy as np, pandas as pd\nfrom scipy.stats import spearmanr\nROOT=Path('/Users/home1/esg-dart-project')\nsys.path.insert(0, str(ROOT/'analysis'))\nimport synth_lib as S\nns = runpy.run_path(str(ROOT/'analysis/11_defense_additional.py'))\nglobals().update({k:v for k,v in ns.items() if not k.startswith('__')})\nm=S.load_synthesis()\nprint(m.shape)")
    md("## A-1. LMG/Shapley")
    code("lmg = exact_lmg(m, S.INTEG_GRADE, GROUPS)\ndisplay(pd.read_csv(ROOT/'data/processed/07d_a1_hierarchical_r2.csv'))\ndisplay(lmg)")
    md("## A-2. 다중검정 보정")
    code("fc = pd.read_csv(ROOT/'data/processed/07d_a3_fullcontrol_coef.csv')\nadj = p_adjust(fc['p']).reset_index(drop=True)\ndisplay(pd.concat([fc[['label','dim','coef','p']], adj[['p_bonferroni','p_bh_fdr']]], axis=1))")
    md("## A-3. 텍스트 점수 x 규모/분량 상관")
    code("display(text_size_correlations(m).pivot(index='score', columns='target', values='rho'))")
    md("## A-4. 금융업 제외")
    code("nofin = m[m['sector']!='금융·보험'].copy()\ndisplay(hierarchical(nofin))\ndisplay(fullcontrol_coef(nofin))")
    md("## A-5/B-5/D-1")
    code("display(dimension_size_r2(m))\ndisplay(industry_distribution(m))\nnum = number_density_optional(m)\ndisplay(num.head())")
    nb["cells"] = cells
    nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}
    nbf.write(nb, NB)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    m = S.load_synthesis()
    tables: dict[str, pd.DataFrame] = {}

    tables["lmg_shapley"] = exact_lmg(m, S.INTEG_GRADE, GROUPS)
    tables["lmg_shapley"].to_csv(DP / "11_defense_lmg_shapley.csv", index=False)

    fc = pd.read_csv(DP / "07d_a3_fullcontrol_coef.csv")
    tables["table5_adjusted"] = pd.concat([fc.reset_index(drop=True), p_adjust(fc["p"])], axis=1)
    tables["table5_adjusted"].to_csv(DP / "11_defense_table5_p_adjusted.csv", index=False)

    tables["text_size_corr"] = text_size_correlations(m)
    tables["text_size_corr"].to_csv(DP / "11_defense_text_size_correlations.csv", index=False)

    nofin = m[m["sector"] != "금융·보험"].copy()
    tables["finance_excluded_hierarchical"] = hierarchical(nofin)
    tables["finance_excluded_hierarchical"].to_csv(DP / "11_defense_finance_excluded_hierarchical_r2.csv", index=False)
    tables["finance_excluded_fullcontrol"] = fullcontrol_coef(nofin)
    tables["finance_excluded_fullcontrol"].to_csv(DP / "11_defense_finance_excluded_fullcontrol.csv", index=False)

    tables["dimension_size_r2"] = dimension_size_r2(m)
    tables["dimension_size_r2"].to_csv(DP / "11_defense_dimension_size_r2.csv", index=False)

    tables["industry_distribution"] = industry_distribution(m)
    tables["industry_distribution"].to_csv(DP / "11_defense_industry_distribution.csv", index=False)

    num = number_density_optional(m)
    num.to_csv(DP / "11_defense_number_density.csv", index=False)
    num_corr = []
    for y in ["log_assets", "esg_grade_num", "e_grade", "s_grade", "g_grade"]:
        r = spearmanr(num["numeric_density_per_1k_char"], num[y], nan_policy="omit")
        num_corr.append({"x": "numeric_density_per_1k_char", "y": y, "rho": r.statistic, "p": r.pvalue})
    pd.DataFrame(num_corr).to_csv(DP / "11_defense_number_density_correlations.csv", index=False)

    (OUT / "11_defense_summary.md").write_text(summarize(m, tables), encoding="utf-8")
    build_notebook()

    print("wrote:")
    for p in sorted(DP.glob("11_defense_*.csv")):
        print(" -", p)
    print(" -", OUT / "11_defense_summary.md")
    print(" -", NB)


if __name__ == "__main__":
    main()
