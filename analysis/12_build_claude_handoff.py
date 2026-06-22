"""Build a portable Claude Desktop handoff package for defense writing.

The package is intentionally self-contained:
- one detailed Markdown file with relative image/table links
- copied PNG figures under figures/
- copied CSV evidence under tables/
- lightweight PNG summaries for the newly computed defense analyses
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-codex")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path("/Users/home1/esg-dart-project")
DP = ROOT / "data/processed"
REPORT_FIG = ROOT / "reports/figures"
PRES_FIG = ROOT / "reports/presentation_figures"
OUT = ROOT / "outputs/claude_defense_handoff"
FIG = OUT / "figures"
TBL = OUT / "tables"


plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


TABLES = [
    "company_controls.csv",
    "07d_a1_hierarchical_r2.csv",
    "07d_a3_fullcontrol_coef.csv",
    "07d_a3_meta_survival.csv",
    "07d_a4_length_myth.csv",
    "07d_a5_industry_profile.csv",
    "07d_a6_signal_ci.csv",
    "08_h1_esg_decomposition.csv",
    "08_h2_keyword_density_corr.csv",
    "08_h2_top_vs_bottom.csv",
    "08_h3_dimension_summary.csv",
    "08_h4_cross_track_convergence.csv",
    "08_h4_dimension_separation.csv",
    "08_h4_length_sensitivity.csv",
    "11_defense_lmg_shapley.csv",
    "11_defense_table5_p_adjusted.csv",
    "11_defense_text_size_correlations.csv",
    "11_defense_finance_excluded_hierarchical_r2.csv",
    "11_defense_finance_excluded_fullcontrol.csv",
    "11_defense_dimension_size_r2.csv",
    "11_defense_industry_distribution.csv",
    "11_defense_number_density_correlations.csv",
]

FIGURES = {
    "fig02_size_first.png": PRES_FIG / "fig02_size_first.png",
    "fig04_survival_matrix.png": PRES_FIG / "fig04_survival_matrix.png",
    "fig05_driver_boiler.png": PRES_FIG / "fig05_driver_boiler.png",
    "fig06_tfidf_vs_dense.png": PRES_FIG / "fig06_tfidf_vs_dense.png",
    "fig07_quadrant.png": PRES_FIG / "fig07_quadrant.png",
    "fig08_forest_ci.png": PRES_FIG / "fig08_forest_ci.png",
    "fig08b_se_coef.png": PRES_FIG / "fig08b_se_coef.png",
    "07d_a1_block_increments.png": REPORT_FIG / "07d_a1_block_increments.png",
    "07d_a3_convergence_heatmap.png": REPORT_FIG / "07d_a3_convergence_heatmap.png",
    "07d_a4_length_myth.png": REPORT_FIG / "07d_a4_length_myth.png",
    "07d_a5_industry_effects.png": REPORT_FIG / "07d_a5_industry_effects.png",
    "08_h1_kcgs_structure.png": REPORT_FIG / "08_h1_kcgs_structure.png",
    "08_h2_measurability.png": REPORT_FIG / "08_h2_measurability.png",
    "08_h3_dictionary_quality.png": REPORT_FIG / "08_h3_dictionary_quality.png",
    "08_h4_dense_failure.png": REPORT_FIG / "08_h4_dense_failure.png",
}


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def fmt_p(x: float) -> str:
    if pd.isna(x):
        return ""
    if x < 0.001:
        return f"{x:.2e}"
    return f"{x:.3f}"


def copy_inputs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    TBL.mkdir(exist_ok=True)
    for name in TABLES:
        src = DP / name
        if src.exists():
            shutil.copy2(src, TBL / name)
    for name, src in FIGURES.items():
        if src.exists():
            shutil.copy2(src, FIG / name)


def save_defense_figures() -> None:
    lmg = pd.read_csv(DP / "11_defense_lmg_shapley.csv")
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    lmg = lmg.sort_values("ols_lmg", ascending=True)
    ax.barh(lmg["variable"], lmg["ols_lmg"], color=["#95A5A6", "#95A5A6", "#95A5A6", "#34495E"])
    for y, v, s in zip(lmg["variable"], lmg["ols_lmg"], lmg["ols_share"]):
        ax.text(v + 0.006, y, f"{v:.3f} ({s:.1%})", va="center", fontsize=10)
    ax.set_title("LMG/Shapley 순서평균 기여도: 규모가 최대")
    ax.set_xlabel("OLS R² contribution")
    ax.set_xlim(0, max(lmg["ols_lmg"]) * 1.35)
    fig.tight_layout()
    fig.savefig(FIG / "11_a1_lmg_shapley.png", dpi=180)
    plt.close(fig)

    adj = pd.read_csv(DP / "11_defense_table5_p_adjusted.csv")
    adj["test"] = adj["label"].str.replace("① ", "", regex=False).str.replace("② ", "", regex=False).str.replace("③ ", "", regex=False) + "-" + adj["dim"]
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    x = np.arange(len(adj))
    ax.scatter(x, adj["p_raw"], label="원 p", color="#95A5A6", s=38)
    ax.scatter(x, adj["p_bh_fdr"], label="BH-FDR q", color="#2563EB", s=38)
    ax.axhline(0.05, color="#E15759", lw=1.0, ls="--")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(adj["test"], rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("p / q (log scale)")
    ax.set_title("Table 5 다중검정 보정: 전역 BH-FDR 생존은 seed-G만")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "11_a2_multiple_testing.png", dpi=180)
    plt.close(fig)

    corr = pd.read_csv(DP / "11_defense_text_size_correlations.csv")
    mat = corr.pivot(index="score", columns="target", values="rho")
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    im = ax.imshow(mat.values, cmap="RdBu_r", vmin=-0.75, vmax=0.75)
    ax.set_xticks(range(mat.shape[1]))
    ax.set_xticklabels(mat.columns, rotation=20, ha="right")
    ax.set_yticks(range(mat.shape[0]))
    ax.set_yticklabels(mat.index, fontsize=8)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat.iloc[i, j]
            ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=8, color="white" if abs(v) > 0.45 else "black")
    ax.set_title("텍스트 점수와 규모/분량 Spearman rho")
    fig.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    fig.savefig(FIG / "11_a3_text_size_correlation.png", dpi=180)
    plt.close(fig)

    dim = pd.read_csv(DP / "11_defense_dimension_size_r2.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.bar(dim["dimension"], dim["ols_r2"], color=["#55A868", "#4C72B0", "#C44E52"])
    for x, y in zip(dim["dimension"], dim["ols_r2"]):
        ax.text(x, y + 0.015, f"{y:.3f}", ha="center", fontsize=11)
    ax.set_ylim(0, 0.52)
    ax.set_ylabel("OLS R²")
    ax.set_title("차원별 규모 단독 설명력: G만의 문제가 아님")
    fig.tight_layout()
    fig.savefig(FIG / "11_a5_dimension_size_r2.png", dpi=180)
    plt.close(fig)


def md_table(df: pd.DataFrame, cols: list[str] | None = None, n: int | None = None) -> str:
    if cols:
        df = df[cols]
    if n:
        df = df.head(n)
    work = df.copy()
    work = work.fillna("")
    headers = [str(c) for c in work.columns]
    rows = [[str(v) for v in row] for row in work.to_numpy()]
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(v)) for w, v in zip(widths, row)]
    head = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |"
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    body = ["| " + " | ".join(v.ljust(w) for v, w in zip(row, widths)) + " |" for row in rows]
    return "\n".join([head, sep] + body)


def build_markdown() -> str:
    h = pd.read_csv(DP / "07d_a1_hierarchical_r2.csv")
    lmg = pd.read_csv(DP / "11_defense_lmg_shapley.csv")
    adj = pd.read_csv(DP / "11_defense_table5_p_adjusted.csv")
    corr = pd.read_csv(DP / "11_defense_text_size_correlations.csv")
    nofin_h = pd.read_csv(DP / "11_defense_finance_excluded_hierarchical_r2.csv")
    nofin_fc = pd.read_csv(DP / "11_defense_finance_excluded_fullcontrol.csv")
    orig_fc = pd.read_csv(DP / "07d_a3_fullcontrol_coef.csv")
    dim = pd.read_csv(DP / "11_defense_dimension_size_r2.csv")
    ind = pd.read_csv(DP / "11_defense_industry_distribution.csv")
    num = pd.read_csv(DP / "11_defense_number_density_correlations.csv")
    controls = pd.read_csv(DP / "company_controls.csv")
    kcgs_decomp = pd.read_csv(DP / "08_h1_esg_decomposition.csv")
    h2_corr = pd.read_csv(DP / "08_h2_keyword_density_corr.csv")
    h2_top = pd.read_csv(DP / "08_h2_top_vs_bottom.csv")
    h3 = pd.read_csv(DP / "08_h3_dimension_summary.csv")
    h4_sep = pd.read_csv(DP / "08_h4_dimension_separation.csv")
    h4_conv = pd.read_csv(DP / "08_h4_cross_track_convergence.csv")

    adj_show = adj[["label", "dim", "coef", "p_raw", "p_bonferroni", "p_bh_fdr"]].copy()
    for c in ["p_raw", "p_bonferroni", "p_bh_fdr"]:
        adj_show[c] = adj_show[c].map(fmt_p)
    corr_show = corr.copy()
    corr_show["rho"] = corr_show["rho"].map(lambda x: f"{x:.3f}")
    corr_show["p"] = corr_show["p"].map(fmt_p)

    comp = orig_fc.merge(nofin_fc, on=["repr", "label", "dim"], suffixes=("_orig", "_nofin"))
    comp = comp[["label", "dim", "coef_orig", "p_orig", "coef_nofin", "p_nofin"]].copy()
    for c in ["coef_orig", "coef_nofin"]:
        comp[c] = comp[c].map(lambda x: f"{x:.3f}")
    for c in ["p_orig", "p_nofin"]:
        comp[c] = comp[c].map(fmt_p)

    dim_show = dim.copy()
    dim_show["ols_r2"] = dim_show["ols_r2"].map(lambda x: f"{x:.3f}")
    dim_show["mcfadden"] = dim_show["mcfadden"].map(lambda x: f"{x:.3f}")
    dim_show["ordered_coef_size"] = dim_show["ordered_coef_size"].map(lambda x: f"{x:.3f}")
    dim_show["ols_p_size"] = dim_show["ols_p_size"].map(fmt_p)
    dim_show["ordered_p_size"] = dim_show["ordered_p_size"].map(fmt_p)

    lmg_show = lmg.copy()
    for c in ["ols_lmg", "mcf_lmg", "ols_min", "ols_max", "mcf_min", "mcf_max"]:
        lmg_show[c] = lmg_show[c].map(lambda x: f"{x:.3f}")
    lmg_show["ols_share"] = lmg_show["ols_share"].map(lambda x: f"{x:.1%}")
    lmg_show["mcf_share"] = lmg_show["mcf_share"].map(lambda x: f"{x:.1%}")

    asset_dist = controls["assets_fs_div"].value_counts(dropna=False).rename_axis("assets_fs_div").reset_index(name="n")
    asset_dist["share"] = asset_dist["n"] / asset_dist["n"].sum()
    asset_dist["share"] = asset_dist["share"].map(lambda x: f"{x:.1%}")

    ind_show = ind.copy()
    ind_show["ratio"] = ind_show["ratio"].map(lambda x: f"{x:.1%}")

    nofin_h_show = nofin_h.copy()
    for c in ["ols_r2", "ols_dr2", "mcfadden", "mcf_dr2"]:
        nofin_h_show[c] = nofin_h_show[c].map(lambda x: f"{x:.3f}")

    finance_n = int(ind.loc[ind["sector"] == "금융·보험", "company_years"].iloc[0])
    nonfinance_n = int(381 - finance_n)
    seed_g = comp[(comp["label"] == "① seed TF-IDF") & (comp["dim"] == "G")].iloc[0]
    sup_s = comp[(comp["label"] == "③ dense supervised") & (comp["dim"] == "S")].iloc[0]

    return f"""# Claude Desktop 전달용: 논문 방어 추가분석 패키지

이 폴더는 Claude Desktop에서 프로젝트 데이터에 접근하지 못하는 상황을 전제로 만든 **전달용 근거 묶음**입니다. 이 Markdown 하나와 `figures/`, `tables/` 폴더를 같이 전달하면 됩니다.

## 사용법

1. Claude Desktop에 이 파일 `CLAUDE_HANDOFF.md`를 붙여넣거나 업로드합니다.
2. 그림이 필요한 경우 이 폴더 전체(`outputs/claude_defense_handoff`)를 같이 전달합니다. 이미지 링크는 모두 상대경로입니다.
3. CSV 원자료가 필요하면 `tables/` 안의 파일을 첨부하면 됩니다.

## 한 줄 결론

- 필수 추가 분석 5건은 모두 완료했습니다.
- 가장 방어력이 큰 결과는 다음 4개입니다.
- **규모 효과는 순서 의존성 검증 후에도 최대**입니다: 기존 순차투입 규모 ΔR²={h.iloc[0]["ols_dr2"]:.3f}, LMG/Shapley OLS 기여도 규모={lmg.loc[lmg.variable=="규모", "ols_lmg"].iloc[0]:.3f}({lmg.loc[lmg.variable=="규모", "ols_share"].iloc[0]:.1%}).
- **다중검정 전역 보정 후 생존은 seed-G 하나**입니다: seed-G β=0.378, BH-FDR q=0.041. supervised-S는 원 p=0.013이지만 전역 BH-FDR q=0.078로 경계/탈락입니다.
- **금융업 제외 후에도 결론은 유지**됩니다: 표본 381→{nonfinance_n}, seed-G β {seed_g.coef_orig}(p={seed_g.p_orig})→{seed_g.coef_nofin}(p={seed_g.p_nofin}), supervised-S β {sup_s.coef_orig}(p={sup_s.p_orig})→{sup_s.coef_nofin}(p={sup_s.p_nofin}).
- **규모 설명력은 G만의 현상이 아닙니다**: E R²=0.444, S R²=0.400, G R²=0.362.

## Claude에게 바로 줄 작업 지시문

아래 분석 결과를 논문 방어용 수정에 반영해줘. 단, 모든 결론은 "KCGS 등급과의 연관"으로 한정하고, 인과 표현은 쓰지 말아줘. 핵심 수정 위치는 3-4 금융업 제외 강건성, 4-6 차원별 규모 설명력, 5-1 LMG/Shapley, 5-2 다중검정 보정, 6-2 텍스트 점수와 규모/분량 상관표야. 그림은 이 Markdown의 상대 링크를 사용해 부록 또는 발표용 보조자료에 넣어줘.

---

# A. 필수 추가 분석

## A-1. LMG/Shapley 상대기여도 분석

**발견 여부**: 새로 계산 완료.  
**목적**: Table 4의 "규모 단독 43.3%"가 순차투입 순서에만 의존하는지 검증.  
**관련 파일**: [`tables/11_defense_lmg_shapley.csv`](tables/11_defense_lmg_shapley.csv), [`tables/07d_a1_hierarchical_r2.csv`](tables/07d_a1_hierarchical_r2.csv)  
**논문 반영 위치**: 5-1, Table 4 주석 또는 부록 표.

![LMG/Shapley](figures/11_a1_lmg_shapley.png)

### 기존 순차투입 결과

{md_table(h[["block", "kind", "ols_r2", "ols_dr2", "mcfadden", "mcf_dr2"]])}

### LMG/Shapley 순서평균 기여도

{md_table(lmg_show[["variable", "ols_lmg", "ols_share", "mcf_lmg", "mcf_share", "ols_min", "ols_max"]])}

**핵심 해석**: 순차투입에서는 규모가 처음 들어가므로 ΔR²=0.433으로 매우 크게 보일 수 있다. 하지만 4개 블록의 24개 순서를 평균한 LMG/Shapley에서도 규모가 OLS 기여도 0.236, share 46.6%로 최대다. 따라서 "규모 우위가 투입 순서의 산물"이라는 공격은 약해진다.

**논문용 문장**:  
> Table 4의 순차투입 결과가 투입 순서에 민감할 수 있다는 점을 고려하여 규모·분량·업종·연도 4개 블록의 모든 순열(4!=24)에 대한 LMG/Shapley 분해를 추가하였다. 그 결과 순서평균 OLS 기여도는 규모 0.236, 분량 0.201, 업종 0.069, 연도 0.001로, 순서를 평균해도 규모가 가장 큰 설명 블록으로 유지되었다.

## A-2. 다중검정 보정

**발견 여부**: 새로 계산 완료.  
**목적**: Table 5의 12개 자기차원 완전통제 검정에 Bonferroni와 Benjamini-Hochberg FDR 적용.  
**관련 파일**: [`tables/11_defense_table5_p_adjusted.csv`](tables/11_defense_table5_p_adjusted.csv), 원본 [`tables/07d_a3_fullcontrol_coef.csv`](tables/07d_a3_fullcontrol_coef.csv)  
**논문 반영 위치**: 5-2, Table 5 주석/부록.

![Multiple testing](figures/11_a2_multiple_testing.png)

{md_table(adj_show)}

**생존 신호 목록**

- 전역 Bonferroni(m=12): seed TF-IDF-G만 생존. p=0.0034 → 보정 p=0.0408.
- 전역 BH-FDR(q=.05): seed TF-IDF-G만 생존. q=0.0408.
- supervised-S는 원 p=0.013으로 유의하지만 전역 Bonferroni p=0.156, BH-FDR q=0.078로 보정 후 5% 기준에서는 생존하지 않는다.

**논문용 문장**:  
> 12개 자기차원 텍스트 검정에 대한 전역 다중검정 보정을 적용하면, Bonferroni와 BH-FDR 모두에서 생존하는 신호는 seed TF-IDF의 G뿐이다(β=0.378, BH-FDR q=.041). supervised-S는 원 p값 기준으로는 유의하지만 전역 보정 후에는 q=.078로 경계적 신호에 그친다.

## A-3. 텍스트 점수 × 규모 상관표

**발견 여부**: 새로 계산 완료.  
**목적**: "텍스트 점수의 규모 편향" 주장 근거 확보.  
**관련 파일**: [`tables/11_defense_text_size_correlations.csv`](tables/11_defense_text_size_correlations.csv)  
**논문 반영 위치**: 6-2, 규모 편향 근거 표.

![Text-size correlation](figures/11_a3_text_size_correlation.png)

{md_table(corr_show)}

**핵심 해석**: 텍스트 점수 상당수가 log(total_assets), log(document_length)와 강한 양의 순위상관을 갖는다. 특히 supervised 점수는 규모/분량 상관이 매우 높고, seed-G도 log_assets rho=0.600, log_length rho=0.542로 높다. 따라서 "텍스트 점수가 ESG 차원만이 아니라 규모·공시 분량을 함께 담는다"는 주장은 데이터로 방어 가능하다.

**논문용 문장**:  
> 12개 텍스트 점수와 규모·분량의 Spearman 상관을 계산한 결과, 다수의 점수가 log(total assets) 및 log(document length)와 유의한 양의 상관을 보였다. 이는 본 논문에서 말하는 규모 편향이 등급의 가치판단이 아니라, 텍스트 점수 자체가 기업 규모와 공시 분량의 분산을 체계적으로 포함한다는 측정상의 주장임을 뒷받침한다.

## A-4. 금융업 제외 강건성

**발견 여부**: 새로 계산 완료.  
**목적**: 금융·보험 업종이 규모 효과나 G/S 신호를 주도하는지 확인.  
**관련 파일**: [`tables/11_defense_finance_excluded_hierarchical_r2.csv`](tables/11_defense_finance_excluded_hierarchical_r2.csv), [`tables/11_defense_finance_excluded_fullcontrol.csv`](tables/11_defense_finance_excluded_fullcontrol.csv)  
**논문 반영 위치**: 3-4, 강건성 부록.

### 금융업 제외 후 Table 4 재추정

{md_table(nofin_h_show)}

### 원본 vs 금융업 제외: Table 5 자기차원 완전통제 계수

{md_table(comp)}

**특히 중요한 비교**

- 표본: 전체 381 기업-연도 → 금융·보험 78건 제외 후 {nonfinance_n} 기업-연도.
- 규모 ΔR²: 0.433 → {nofin_h.iloc[0]["ols_dr2"]:.3f}. 금융업 제외 후에도 오히려 커진다.
- seed-G: β {seed_g.coef_orig}(p={seed_g.p_orig}) → {seed_g.coef_nofin}(p={seed_g.p_nofin}). 유지.
- supervised-S: β {sup_s.coef_orig}(p={sup_s.p_orig}) → {sup_s.coef_nofin}(p={sup_s.p_nofin}). 유지.
- 추가 관찰: 금융 제외 후 expanded-G가 β=0.621, p=.0008로 유의해진다. 본문 핵심 결론에는 "금융업 제외 후에도 G 계열 사전 기반 신호는 유지/강화" 정도로 조심스럽게 반영하고, 전역 원표본의 주결론을 대체하지는 않는 것이 안전하다.

**논문용 문장**:  
> 금융·보험 업종 78개 기업-연도를 제외하고 동일한 위계 회귀와 자기차원 완전통제 모형을 재추정한 결과, 규모 단독 설명력은 0.433에서 0.502로 유지·증가했고, 원표본의 핵심 생존 신호인 seed-G와 supervised-S도 각각 β=0.406(p=.004), β=0.637(p=.017)로 유지되었다. 따라서 본 결과가 금융업 표본만에 의해 주도된다는 해석은 지지되지 않는다.

## A-5. 차원별 규모 설명력

**발견 여부**: 새로 계산 완료.  
**목적**: "G만 규모를 반영하는가?" 확인.  
**관련 파일**: [`tables/11_defense_dimension_size_r2.csv`](tables/11_defense_dimension_size_r2.csv)  
**논문 반영 위치**: 4-6, 규모 편향/통합등급 방어.

![Dimension size R2](figures/11_a5_dimension_size_r2.png)

{md_table(dim_show[["dimension", "target", "ols_r2", "ols_p_size", "mcfadden", "ordered_p_size", "ordered_coef_size"]])}

**핵심 해석**: 규모 설명력은 G 특유가 아니라 E/S/G 전반에서 크다. 오히려 OLS R²는 E가 0.444로 가장 높고, S 0.400, G 0.362 순이다. 따라서 "통합등급이 G에 가깝기 때문에 규모 편향이 보인다"는 공격에는, 분리 등급에서도 규모 효과가 크다고 답하면 된다.

**논문용 문장**:  
> 규모 단독 설명력은 통합등급뿐 아니라 E/S/G 분리 등급에서도 크게 나타난다(E R²=.444, S R²=.400, G R²=.362). 따라서 규모 의존성은 통합등급의 G 편향만으로 환원되기보다, KCGS 분리 등급 전반에 걸친 구조적 공변 요인으로 해석하는 것이 타당하다.

---

# B. 확인 작업

## B-1. 총자산 변수 확인

**발견 여부**: 확인 완료.  
**관련 파일**: [`tables/company_controls.csv`](tables/company_controls.csv), 요약 표는 아래.  
**논문 반영 위치**: 자료/변수 정의 각주.

{md_table(asset_dist)}

**최종 기준**: `log_assets`는 `assets`의 자연로그다. 기준은 **연결재무제표(CFS) 우선**이며, 자동 추출 CFS 345건 + 수작업 보완 CFS_MANUAL 18건 + OFS fallback 18건이 포함된다. 따라서 "전부 연결 기준"이라고 쓰면 안 되고, "연결 우선, 일부 별도 fallback 포함"이라고 써야 한다.

**논문용 문장**:  
> 총자산 변수는 DART 재무제표의 자산총계를 사용하되 연결재무제표(CFS)를 우선 적용하였다. 최종 표본에서는 CFS 345건, 수작업 보완 CFS 18건, 연결값을 확보하지 못한 OFS fallback 18건이 포함되며, 회귀에는 이 자산총계의 자연로그를 사용하였다.

## B-2. "아홉 가지 점수" 확인

**발견 여부**: 확인 완료.  
**관련 파일**: `analysis/synth_lib.py`, [`tables/07d_a3_fullcontrol_coef.csv`](tables/07d_a3_fullcontrol_coef.csv)  
**논문 반영 위치**: 측정치 구성 설명.

**9개 점수의 정확한 구성**

- 포함: seed TF-IDF 3개 = `tfidf_E`, `tfidf_S`, `tfidf_G`
- 포함: fastText 확장 TF-IDF 3개 = `expanded_tfidf_E`, `expanded_tfidf_S`, `expanded_tfidf_G`
- 포함: dense cosine 3개 = `E_cos`, `S_cos`, `G_cos`
- 제외/별도: dense supervised 3개 = `E_sup`, `S_sup`, `G_sup`

**제외 이유**: supervised는 등급 정보를 학습한 OOF 상한/검증 점수이므로, 비지도 텍스트 점수 9개와 같은 범주로 묶으면 순환성 논란이 생긴다. 따라서 논문에서는 "비지도 9개 + 지도 상한 3개"로 분리하는 것이 가장 안전하다.

## B-3. KCGS 등급 연도 매칭 확인

**발견 여부**: 확인 완료.  
**관련 파일**: `notebooks/보고용_분석노트북.ipynb`, `plan/04_preprocessing.md`, `analysis/synth_lib.py`  
**논문 반영 위치**: 데이터 매칭/식별 전략.

**실제 merge 규칙**

- `doc_id = {{stock_code 6자리}}_{{fiscal_year}}`
- `esg_year = fiscal_year + 1`
- 예: 2022 사업보고서 → 2023 KCGS 등급, 2023 사업보고서 → 2024 KCGS 등급, 2024 사업보고서 → 2025 KCGS 등급
- join key는 회사명 단독이 아니라 `company_name + esg_year`, 최종 분석에서는 `doc_id` 기준 1:1 병합.

**논문용 문장**:  
> 사업보고서는 회계연도 종료 후 익년에 공시되고 KCGS 등급도 익년 평가 사이클에서 발표되므로, 본 연구는 `esg_year = fiscal_year + 1` 규칙으로 사업보고서와 KCGS 등급을 매칭하였다. 최종 분석 단위는 `doc_id = stock_code_fiscal_year`이며, 회사명 단독 병합은 사용하지 않았다.

## B-4. KCGS 평가체계 개정 여부

**발견 여부**: 내부 프로젝트 자료에서는 분석기간 중 평가체계 개정 사실을 직접 입증하는 파일을 찾지 못했다.  
**관련 파일**: `협업가이드자료/KCGS_ESG_평가방법론_정리.md`, `조언.md`  
**논문 반영 위치**: 한계/자료 설명.

**권장 방어**: "내부 자료 기준으로는 평가체계 변경 여부를 독립적으로 검증하지 못했으며, 연도 더미로 공통 연도 충격을 통제했다"라고 쓰는 것이 안전하다.

## B-5. 업종 분포

**발견 여부**: 계산 완료.  
**관련 파일**: [`tables/11_defense_industry_distribution.csv`](tables/11_defense_industry_distribution.csv)  
**논문 반영 위치**: 표본 설명/Table 1.

{md_table(ind_show)}

---

# C. 이미 계산된 강건성/기록

## C-1. max_df=1.0 강건성

**발견 여부**: 기존 문서에서 확인.  
**관련 파일**: `analysis/_build_notebook.py`, `outputs/발표자료_v2.md`  
**핵심 수치**: seed-G 계수는 기본 max_df=0.95에서 β≈0.38, max_df=1.0 재구성에서도 β≈0.51로 유지된다고 기록되어 있다.

**논문 반영 위치**: 4.3 또는 G 결과 주석.  
**방어 문장**:  
> seed-G 결과는 특정 max_df 설정의 산물이 아니다. max_df=1.0으로 흔한 G 어휘를 복귀시켜 사전을 재구성해도 G 계수는 유지되며, 이는 특정 어휘 목록이나 vocabulary pruning의 인공물이라는 해석을 약화시킨다.

## C-2. 앵커 교체/ABTT/whitening

**발견 여부**: 기존 설계 기록 확인.  
**관련 파일**: `plan/01_rationale.md`, `notebooks/07b_dense_esg_v2_colab.ipynb`, 그림 [`figures/08_h4_dense_failure.png`](figures/08_h4_dense_failure.png)  
**논문 반영 위치**: dense 방법론/한계.

![Dense failure](figures/08_h4_dense_failure.png)

**핵심 해석**: dense cosine은 ABTT/whitening, 하위차원 앵커, 길이강건 풀링을 적용했지만 G에서 seed TF-IDF와 수렴하지 못했다. 따라서 dense 실패는 단순히 전처리 부재가 아니라 범용 임베딩의 차원분리 한계로 해석된다.

## C-3. OOF 검증

**발견 여부**: 기존 기록 확인.  
**관련 파일**: `outputs/final_report_detailed.html`, `notebooks/07b_dense_esg_v2_colab.ipynb`  
**핵심 내용**: supervised probe는 기업 단위 GroupKFold OOF 예측을 사용했고, 같은 기업이 학습·검증에 동시에 들어가지 않도록 그룹 누설을 방지했다.

**논문 반영 위치**: supervised 점수 설명/Table 5 주석.  
**방어 문장**:  
> supervised 점수는 등급 정보를 사용하는 상한 진단이므로 비지도 점수와 동일한 증거 지위로 해석하지 않는다. 다만 예측값은 기업 단위 GroupKFold의 out-of-fold 예측으로 생성하여 동일 기업의 학습-검증 누설을 방지했다.

## C-4. 4.3 사례분석 기록: DRIVER vs BOILER

**발견 여부**: 기존 산출물 확인.  
**관련 파일**: [`tables/08_h2_keyword_density_corr.csv`](tables/08_h2_keyword_density_corr.csv), [`tables/08_h2_top_vs_bottom.csv`](tables/08_h2_top_vs_bottom.csv), 그림 [`figures/fig05_driver_boiler.png`](figures/fig05_driver_boiler.png)

![Driver boiler](figures/fig05_driver_boiler.png)

### 밀도 상관

{md_table(h2_corr)}

### 상하위 10 기업 비교

{md_table(h2_top)}

**논문 반영 위치**: 4.3 부록/사례분석.  
**핵심 해석**: DRIVER(윤리·준법·컴플라이언스·부패방지) 밀도는 tfidf_G 및 G등급과 양의 관계를 보이고, BOILERPLATE(이사회·사외이사·감사위원·주주총회)는 등급과 반대 또는 약한 관계를 보인다. 이 분석은 탐색적 메커니즘 설명이며, 본증거는 완전통제 회귀다.

---

# D. 선택 분석

## D-1. 숫자 밀도 변수

**발견 여부**: 선택 분석으로 계산 완료.  
**관련 파일**: [`tables/11_defense_number_density_correlations.csv`](tables/11_defense_number_density_correlations.csv)  
**논문 반영 위치**: 후속 과제 또는 부록.

{md_table(num)}

**해석 주의**: 단순 숫자/단위 토큰 밀도는 규모와 약한 음의 상관(rho=-0.106), 등급과도 음의 상관을 보인다. 즉 "숫자가 많으면 등급이 높다"는 단순 가설은 현재 단순 밀도 지표로는 지지되지 않는다. 다만 이 지표는 전체 사업보고서의 모든 숫자를 포함하므로 재무표/임원표 등 비ESG 숫자까지 섞인다. E 정량공시만 분리하려면 섹션/문장 단위 정교화가 필요하다.

## D-2. 섹션 × ESG 차원 분포

**발견 여부**: 이번 패키지에서는 신규 계산하지 않음.  
**관련 기존 파일**: `data/processed/dart_section_lengths.csv`, `협업가이드자료/섹션_선택_근거.md`  
**논문 반영 위치**: 선택 부록.  
**권장 처리**: 시간이 부족하면 본문에는 "II·IV·VI 선택 근거"만 쓰고, 섹션×차원 분포는 후속 과제로 둔다.

## D-3. 문장 수 기준 민감도

**발견 여부**: 기존에 일부 존재.  
**관련 파일**: [`tables/08_h4_length_sensitivity.csv`](tables/08_h4_length_sensitivity.csv), [`tables/07d_a4_length_myth.csv`](tables/07d_a4_length_myth.csv)  
**논문 반영 위치**: 분량 통제 강건성.

![Length myth](figures/07d_a4_length_myth.png)

---

# 보조 그림 묶음

## 규모가 먼저

![Size first](figures/fig02_size_first.png)

## 완전통제 생존 매트릭스

![Survival matrix](figures/fig04_survival_matrix.png)

## TF-IDF vs dense 개념도

![TFIDF vs dense](figures/fig06_tfidf_vs_dense.png)

## 공시량 대비 등급 사분면

![Quadrant](figures/fig07_quadrant.png)

## 약신호 forest CI

![Forest CI](figures/fig08_forest_ci.png)

## S/E 계수 보조 그림

![SE coefficient](figures/fig08b_se_coef.png)

## KCGS 구조 / G 설명 보조 그림

![KCGS structure](figures/08_h1_kcgs_structure.png)

![G measurability](figures/08_h2_measurability.png)

![Dictionary quality](figures/08_h3_dictionary_quality.png)

---

# 논문 수정 우선순위

1. **반드시 넣기**: LMG/Shapley, 다중검정 보정, 금융업 제외, 텍스트×규모 상관, 차원별 규모 R².
2. **문구 정리**: 모든 결론을 "KCGS 등급 기준"으로 한정. "규모 편향"은 텍스트 점수의 측정상 규모 의존성이라고 정의.
3. **supervised-S 처리**: 원 p 기준 유의, 전역 다중검정 후 경계. "보조적/상한적 신호"로 낮춰 쓰기.
4. **seed-G 처리**: 전역 보정 후에도 생존하는 가장 강한 신호. 단, "실제 G 성과"가 아니라 KCGS G등급과의 텍스트 연관으로 한정.
5. **총자산 기준**: 연결 우선, 일부 OFS fallback 포함. "전부 연결"이라고 쓰지 않기.

# 파일 목록

## 핵심 MD

- `CLAUDE_HANDOFF.md`: 지금 보고 있는 전달용 파일

## 핵심 표 CSV

- [`tables/11_defense_lmg_shapley.csv`](tables/11_defense_lmg_shapley.csv)
- [`tables/11_defense_table5_p_adjusted.csv`](tables/11_defense_table5_p_adjusted.csv)
- [`tables/11_defense_text_size_correlations.csv`](tables/11_defense_text_size_correlations.csv)
- [`tables/11_defense_finance_excluded_hierarchical_r2.csv`](tables/11_defense_finance_excluded_hierarchical_r2.csv)
- [`tables/11_defense_finance_excluded_fullcontrol.csv`](tables/11_defense_finance_excluded_fullcontrol.csv)
- [`tables/11_defense_dimension_size_r2.csv`](tables/11_defense_dimension_size_r2.csv)
- [`tables/11_defense_industry_distribution.csv`](tables/11_defense_industry_distribution.csv)

## 핵심 이미지

- [`figures/11_a1_lmg_shapley.png`](figures/11_a1_lmg_shapley.png)
- [`figures/11_a2_multiple_testing.png`](figures/11_a2_multiple_testing.png)
- [`figures/11_a3_text_size_correlation.png`](figures/11_a3_text_size_correlation.png)
- [`figures/11_a5_dimension_size_r2.png`](figures/11_a5_dimension_size_r2.png)
- [`figures/fig02_size_first.png`](figures/fig02_size_first.png)
- [`figures/fig04_survival_matrix.png`](figures/fig04_survival_matrix.png)
- [`figures/fig05_driver_boiler.png`](figures/fig05_driver_boiler.png)
- [`figures/fig08_forest_ci.png`](figures/fig08_forest_ci.png)
"""


def main() -> None:
    copy_inputs()
    save_defense_figures()
    (OUT / "CLAUDE_HANDOFF.md").write_text(build_markdown(), encoding="utf-8")
    (OUT / "README.md").write_text(
        "# Claude defense handoff\n\nStart with `CLAUDE_HANDOFF.md`. Keep `figures/` and `tables/` next to it so relative links work.\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
