"""
07d_synthesis.py — 3트랙 종합 "임팩트 분석" (분석 1~7)
======================================================
기존 산출물(① seed TF-IDF · ② fastText 확장 · ③ dense cos/sup) 위에서만 동작.
개별 트랙 재실행/재인코딩 없음. 통일 통제·기업 cluster SE·z(ddof=0)·인과주장 금지.

각 분석 = ① 표(07d_*.csv) ② 그림(07d_*.png) ③ (해석은 종합_기록.md / 노트북).
실행:  python 07d_synthesis.py [a1 a2 ... | all]
"""
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr, mannwhitneyu

from synth_lib import (
    load_synthesis, fit_ordered, fit_ols, fit_logit, partial_spearman, _resid, setup_font,
    zscore, sig_stars, REPRS, TEXT_COLS, ALL_DIMS, GRADE_COLS, INTEG_GRADE,
    SECTOR_DUMMIES, YEAR_DUMMIES, LEN_Z, SIZE_Z, CTRL_FULL, DP, FIG,
)

plt = setup_font()
REPR_ORDER = ["seed_tfidf", "expanded", "dense_cos", "dense_sup"]
C_CTRL, C_TEXT = "#4C72B0", "#C44E52"
DIM_COLORS = {"E": "#55A868", "S": "#4C72B0", "G": "#C44E52"}
SECTOR_BASE = "1차금속"


def tbl(df, name):
    p = f"{DP}/07d_{name}.csv"
    df.to_csv(p, index=False)
    print(f"  ▸ table  {p}  {df.shape}")
    return df


def savefig(name):
    p = f"{FIG}/07d_{name}.png"
    plt.savefig(p)
    plt.close()
    print(f"  ▸ figure {p}")


def own(repr_key):
    """(dim, raw_col, z_col, grade_col) 4-튜플 리스트 — 자기차원 매칭."""
    return [(d, c, c + "_z", GRADE_COLS[d]) for d, c in zip(ALL_DIMS, REPRS[repr_key]["cols"])]


# ============================================================ 분석 1: 위계적 R² 증분
def a1(m):
    print("\n[분석 1] 위계적 R² 증분 — 텍스트의 점증적 설명력")
    blocks = [
        ("+규모",   [SIZE_Z]),
        ("+분량",   [SIZE_Z, LEN_Z]),
        ("+산업",   [SIZE_Z, LEN_Z] + SECTOR_DUMMIES),
        ("+연도",   [SIZE_Z, LEN_Z] + SECTOR_DUMMIES + YEAR_DUMMIES),
    ]
    full = blocks[-1][1]
    rows = []
    prev_r2 = prev_mcf = 0.0
    for name, cols in blocks:
        ro = fit_ols(m, INTEG_GRADE, cols)
        rl = fit_ordered(m, INTEG_GRADE, cols)
        rows.append(dict(block=name, kind="통제", ols_r2=ro["r2"], ols_dr2=ro["r2"] - prev_r2,
                         mcfadden=rl["mcfadden"], mcf_dr2=rl["mcfadden"] - prev_mcf))
        prev_r2, prev_mcf = ro["r2"], rl["mcfadden"]
    base_r2, base_mcf = prev_r2, prev_mcf
    for rk in REPR_ORDER:
        cols = full + [c + "_z" for c in REPRS[rk]["cols"]]
        ro = fit_ols(m, INTEG_GRADE, cols)
        rl = fit_ordered(m, INTEG_GRADE, cols)
        rows.append(dict(block="+텍스트:" + REPRS[rk]["label"], kind="텍스트",
                         ols_r2=ro["r2"], ols_dr2=ro["r2"] - base_r2,
                         mcfadden=rl["mcfadden"], mcf_dr2=rl["mcfadden"] - base_mcf))
    t = tbl(pd.DataFrame(rows).round(4), "a1_hierarchical_r2")
    print(t.to_string(index=False))

    # 그림: 블록별 ΔR² (OLS / McFadden), 통제 vs 텍스트 색 구분
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, (col, title) in zip(axes, [("ols_dr2", "OLS R² 증분 (ΔR²)"),
                                        ("mcf_dr2", "순서형 McFadden pseudo-R² 증분")]):
        colors = [C_CTRL if k == "통제" else C_TEXT for k in t["kind"]]
        bars = ax.bar(range(len(t)), t[col], color=colors)
        ax.set_xticks(range(len(t)))
        ax.set_xticklabels(t["block"], rotation=40, ha="right", fontsize=8)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel("ΔR²")
        for b, v in zip(bars, t[col]):
            ax.text(b.get_x() + b.get_width() / 2, v + (0.003 if v >= 0 else -0.008),
                    f"{v:+.3f}", ha="center", fontsize=7)
    from matplotlib.patches import Patch
    axes[0].legend(handles=[Patch(color=C_CTRL, label="통제(규모·분량·산업·연도)"),
                            Patch(color=C_TEXT, label="텍스트 추가(트랙별)")], fontsize=8, loc="upper right")
    fig.suptitle("위계적 회귀: 규모가 ΔR²=0.43로 지배 — 텍스트 추가는 ≤0.05(규모의 1/8 이하), dense cosine은 ≈0", fontsize=12)
    fig.tight_layout()
    savefig("a1_block_increments")

    # 그림 2: 텍스트 ΔR²만 (트랙 4종)
    tt = t[t.kind == "텍스트"].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(tt)); w = 0.36
    ax.bar(x - w / 2, tt["ols_dr2"], w, label="OLS ΔR²", color="#C44E52")
    ax.bar(x + w / 2, tt["mcf_dr2"], w, label="McFadden Δpseudo-R²", color="#DD8452")
    for i, r in tt.iterrows():
        ax.text(i - w / 2, r["ols_dr2"] + 0.0008, f"{r['ols_dr2']:+.3f}", ha="center", fontsize=8)
        ax.text(i + w / 2, r["mcf_dr2"] + 0.0008, f"{r['mcf_dr2']:+.3f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([REPRS[k]["label"] for k in REPR_ORDER], fontsize=9)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_title("완전통제 위에 텍스트(E·S·G 3개)를 더했을 때의 설명력 증분 — 규모(0.43)의 1/8 이하, dense cosine은 ≈0", fontsize=11)
    ax.set_ylabel("ΔR² (통제 대비)")
    ax.legend(fontsize=9)
    fig.tight_layout(); savefig("a1_text_deltaR2")
    print(f"  규모 단독 ΔR²(OLS)={t.iloc[0]['ols_dr2']:.3f}; 텍스트 최대 ΔR²(OLS)={tt['ols_dr2'].max():.4f}")


# ============================================================ 분석 2: 잔차 사분면 + 후보
def a2(m):
    print("\n[분석 2] 잔차 분석 — 공시량 대비 등급 사분면 + 과대공시 후보")
    d = m.copy()
    ctrl = [SIZE_Z, LEN_Z] + SECTOR_DUMMIES                      # 텍스트 없이 규모+분량+산업
    ro = fit_ols(d, INTEG_GRADE, ctrl)
    d["pred"] = ro["res"].predict()
    d["resid"] = d[INTEG_GRADE] - d["pred"]
    d["size_bucket"] = pd.qcut(d["log_assets"], 3, labels=["소형", "중형", "대형"])
    txt_show = TEXT_COLS

    # 후보: resid 가장 음(공시·규모 대비 저평가=과대공시 의심) / 가장 양(효율 공시)
    keep = ["doc_id", "stock_code_str", "sector", "size_bucket", "esg_grade", INTEG_GRADE,
            "log_assets", "log_core_doc_len", "log_core_doc_len_z", "resid"] + txt_show
    over = d.nsmallest(10, "resid")[keep].copy()
    eff = d.nlargest(10, "resid")[keep].copy()
    over["label"] = "과대공시(저평가) 의심"; eff["label"] = "효율(저공시·고등급)"
    cand = pd.concat([over, eff], ignore_index=True).round(3)
    tbl(cand, "a2_candidates_raw")

    # 익명화 버전(논문/발표용): doc_id → "{규모} {산업} {알파벳}"
    anon = cand.copy()
    letters = {}
    names = []
    for _, r in anon.iterrows():
        key = (r["size_bucket"], r["sector"])
        letters[key] = letters.get(key, 0) + 1
        names.append(f"{r['size_bucket']} {r['sector']}사 {chr(64 + letters[key])}")
    anon.insert(0, "anon_id", names)
    anon = anon.drop(columns=["doc_id", "stock_code_str"])
    tbl(anon, "a2_candidates_anon")

    # 군간 비교 (과대공시 후보 vs 나머지): Mann-Whitney
    over_ids = set(over["doc_id"])
    g1 = d[d["doc_id"].isin(over_ids)]
    g0 = d[~d["doc_id"].isin(over_ids)]
    comp = []
    for col in ["log_assets", "log_core_doc_len", INTEG_GRADE] + txt_show:
        u, p = mannwhitneyu(g1[col], g0[col], alternative="two-sided")
        comp.append(dict(variable=col, cand_mean=g1[col].mean(), rest_mean=g0[col].mean(),
                         diff=g1[col].mean() - g0[col].mean(), mw_u=u, mw_p=p))
    tbl(pd.DataFrame(comp).round(4), "a2_group_compare")

    # 그림: 사분면 산점도 (공시량 z vs 등급), 색=resid
    fig, ax = plt.subplots(figsize=(9, 6))
    ymed = d[INTEG_GRADE].median()
    sc = ax.scatter(d["log_core_doc_len_z"], d[INTEG_GRADE] + np.random.default_rng(7).normal(0, 0.06, len(d)),
                    c=d["resid"], cmap="RdBu", vmin=-3, vmax=3, s=26, alpha=0.8, edgecolor="gray", linewidth=0.2)
    ax.axvline(0, color="k", lw=0.7, ls="--"); ax.axhline(ymed, color="k", lw=0.7, ls="--")
    ax.scatter(over["log_core_doc_len_z"], over[INTEG_GRADE], s=120, facecolors="none",
               edgecolors="#C44E52", linewidths=1.8, label="과대공시(저평가) 의심 top-10")
    ax.scatter(eff["log_core_doc_len_z"], eff[INTEG_GRADE], s=120, facecolors="none",
               edgecolors="#55A868", linewidths=1.8, label="효율 공시 top-10")
    ax.text(0.98, 0.04, "↘ 우하단: 많이 쓰고 낮은 등급\n(과대공시 의심)", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9, color="#C44E52")
    ax.text(0.02, 0.96, "↖ 좌상단: 적게 쓰고 높은 등급\n(효율 공시)", transform=ax.transAxes,
            ha="left", va="top", fontsize=9, color="#2c6e49")
    ax.set_xlabel("공시량  log(II+IV+VI 문자수) z-score"); ax.set_ylabel("통합 ESG 등급 (0=D ~ 6=S)")
    ax.set_title("공시량 대비 등급 — 사분면 (색=규모·분량·산업 통제 잔차)", fontsize=12)
    plt.colorbar(sc, label="등급 잔차 (양=효율, 음=과대공시 의심)")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout(); savefig("a2_quadrant")
    print(f"  resid 범위 [{d['resid'].min():.2f}, {d['resid'].max():.2f}]; "
          f"과대공시 후보 평균등급 {g1[INTEG_GRADE].mean():.2f} vs 나머지 {g0[INTEG_GRADE].mean():.2f}")


# ============================================================ 분석 3: 표현 간 일치/불일치 (하이라이트)
def a3(m):
    print("\n[분석 3] 표현 방법 간 일치/불일치 — 어느 방법도 같은 차원을 못 가른다")

    # (a) 트랙 간 수렴타당도: 같은 차원끼리 4 표현 Spearman
    conv_rows = []
    for dim in ALL_DIMS:
        cols = {rk: REPRS[rk]["cols"][ALL_DIMS.index(dim)] for rk in REPR_ORDER}
        for i, ra in enumerate(REPR_ORDER):
            for rb in REPR_ORDER[i + 1:]:
                rho = spearmanr(m[cols[ra]], m[cols[rb]]).statistic
                conv_rows.append(dict(dim=dim, repr_a=ra, repr_b=rb,
                                      col_a=cols[ra], col_b=cols[rb], spearman=rho))
    conv = tbl(pd.DataFrame(conv_rows).round(3), "a3_convergence")
    # 핵심: dense cosine × seed tfidf 대각 (committed E.448/S.295/G-.063 재현 확인)
    chk = conv[(conv.repr_a == "seed_tfidf") & (conv.repr_b == "dense_cos")]
    print("  [수렴 재현 확인] seed_tfidf × dense_cos 대각:",
          {r.dim: round(r.spearman, 3) for r in chk.itertuples()}, "(committed E.448/S.295/G-.063)")

    # 12×12 수렴 히트맵
    mat = m[TEXT_COLS].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(9.5, 8))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(TEXT_COLS))); ax.set_yticks(range(len(TEXT_COLS)))
    ax.set_xticklabels(TEXT_COLS, rotation=90, fontsize=7); ax.set_yticklabels(TEXT_COLS, fontsize=7)
    for i in range(len(TEXT_COLS)):
        for j in range(len(TEXT_COLS)):
            ax.text(j, i, f"{mat.iloc[i, j]:.2f}", ha="center", va="center",
                    fontsize=5.5, color="white" if abs(mat.iloc[i, j]) > 0.55 else "black")
    ax.set_title("트랙 간 텍스트 점수 Spearman 상관 (12×12)\n같은 차원끼리도 표현이 다르면 약하게만 수렴", fontsize=11)
    plt.colorbar(im, fraction=0.046)
    fig.tight_layout(); savefig("a3_convergence_heatmap")

    # (b) 부분 3×3 (길이+규모 통제) 4패널
    p3 = []
    for rk in REPR_ORDER:
        cols = REPRS[rk]["cols"]
        for td, tcol in zip(ALL_DIMS, cols):
            for gd in ALL_DIMS:
                rho = partial_spearman(m, tcol, GRADE_COLS[gd], [LEN_Z, SIZE_Z])
                p3.append(dict(repr=rk, text_dim=td, grade_dim=gd, partial_rho=rho))
    p3 = pd.DataFrame(p3)
    tbl(p3.round(3), "a3_partial3x3")
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.3))
    for ax, rk in zip(axes, REPR_ORDER):
        M = p3[p3["repr"] == rk].pivot(index="text_dim", columns="grade_dim", values="partial_rho").loc[ALL_DIMS, ALL_DIMS]
        im = ax.imshow(M, cmap="RdBu_r", vmin=-0.25, vmax=0.25)
        ax.set_xticks(range(3)); ax.set_yticks(range(3))
        ax.set_xticklabels([f"{g}등급" for g in ALL_DIMS]); ax.set_yticklabels([f"{t}텍스트" for t in ALL_DIMS])
        diagdom = sum(M.loc[d].idxmax() == d for d in ALL_DIMS)
        for i, td in enumerate(ALL_DIMS):
            for j, gd in enumerate(ALL_DIMS):
                v = M.loc[td, gd]
                ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=10,
                        fontweight="bold" if td == gd else "normal",
                        color="white" if abs(v) > 0.15 else "black")
        ax.set_title(f"{REPRS[rk]['label']}\n대각지배 {diagdom}/3", fontsize=10)
    fig.suptitle("부분 3×3 Spearman (길이+규모 통제) — 표현마다 대각지배 정도가 다름", fontsize=12)
    fig.tight_layout(); savefig("a3_partial3x3_panels")

    # 대각값 막대
    diag = p3[p3.text_dim == p3.grade_dim]
    fig, ax = plt.subplots(figsize=(8.5, 4.3))
    x = np.arange(3); w = 0.2
    for i, rk in enumerate(REPR_ORDER):
        vals = [diag[(diag["repr"] == rk) & (diag.text_dim == d)]["partial_rho"].iloc[0] for d in ALL_DIMS]
        ax.bar(x + (i - 1.5) * w, vals, w, label=REPRS[rk]["label"])
    ax.set_xticks(x); ax.set_xticklabels([f"{d} (자기차원)" for d in ALL_DIMS])
    ax.axhline(0, color="k", lw=0.6)
    ax.set_title("부분 3×3 대각값(자기차원 부분ρ, 길이+규모 통제)", fontsize=11)
    ax.set_ylabel("부분 Spearman ρ"); ax.legend(fontsize=8)
    fig.tight_layout(); savefig("a3_partial3x3_diagonal")

    # (c) 완전통제 후 자기차원 텍스트 계수 (matched ordered logit)
    fc = []
    for rk in REPR_ORDER:
        for dim, raw, z, gcol in own(rk):
            r = fit_ordered(m, gcol, [z] + CTRL_FULL)
            fc.append(dict(repr=rk, label=REPRS[rk]["label"], dim=dim, coef=r["params"][z],
                           p=r["pvals"][z], ci_low=r["ci_low"][z], ci_high=r["ci_high"][z],
                           sig=sig_stars(r["pvals"][z])))
    fc = pd.DataFrame(fc)
    tbl(fc.round(4), "a3_fullcontrol_coef")
    print("  [완전통제 자기차원 계수]")
    for rk in REPR_ORDER:
        s = fc[fc["repr"] == rk]
        print("   ", REPRS[rk]["label"], {r.dim: f"{r.coef:.2f}{r.sig}" for r in s.itertuples()})
    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(3); w = 0.2
    for i, rk in enumerate(REPR_ORDER):
        s = fc[fc["repr"] == rk].set_index("dim").loc[ALL_DIMS]
        bars = ax.bar(x + (i - 1.5) * w, s["coef"], w, label=REPRS[rk]["label"])
        for b, (_, row) in zip(bars, s.iterrows()):
            if row["sig"]:
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02, row["sig"],
                        ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([f"{d}텍스트→{d}등급" for d in ALL_DIMS])
    ax.axhline(0, color="k", lw=0.6)
    ax.set_title("완전통제(길이·규모·산업·연도) 후 자기차원 텍스트 계수 — 표현마다 다른 1개만 생존", fontsize=11)
    ax.set_ylabel("순서형 로짓 계수 (z, 기업 cluster SE)"); ax.legend(fontsize=8)
    fig.tight_layout(); savefig("a3_fullcontrol_bars")

    # (d) 메타: 차원별 생존 트랙(표현) 수 (p<0.05)
    meta = []
    for dim in ALL_DIMS:
        sub = fc[fc.dim == dim]
        survivors = sub[sub.p < 0.05]
        meta.append(dict(dim=dim, n_repr=len(sub), n_survive_p05=int((sub.p < 0.05).sum()),
                         survivors=", ".join(survivors["label"]) or "(없음)",
                         max_coef=sub["coef"].max(), min_p=sub["p"].min()))
    tbl(pd.DataFrame(meta).round(4), "a3_meta_survival")
    print("  [메타] 차원별 생존(표현) 수:", {r["dim"]: r["n_survive_p05"] for r in meta})


# ============================================================ 분석 4: "긴 보고서=좋은 등급" 검정
def a4(m):
    print("\n[분석 4] '긴 보고서 = 좋은 등급' 통념의 직접 검정·반박")
    rows = []
    for lname, lcol in [("log_core_doc_len(문자수)", "log_core_doc_len"), ("report_len(문장수)", "report_len")]:
        sp = spearmanr(m[lcol], m[INTEG_GRADE]).statistic
        pe = pearsonr(m[lcol], m[INTEG_GRADE])[0]
        psp = partial_spearman(m, lcol, INTEG_GRADE, ["log_assets"])
        # 매개 분해 (z 표준화 OLS): grade ~ len (총효과 c) vs grade ~ len + size (직접효과 c')
        lz = zscore(m[lcol])
        d = m.assign(_lz=lz)
        c = fit_ols(d, INTEG_GRADE, ["_lz"])["params"]["_lz"]
        cprime = fit_ols(d, INTEG_GRADE, ["_lz", SIZE_Z])["params"]["_lz"]
        rows.append(dict(length_def=lname, spearman_raw=sp, pearson_raw=pe,
                         partial_spearman_ctrl_size=psp, drop=sp - psp,
                         coef_total=c, coef_direct=cprime, pct_via_size=(c - cprime) / c))
    t = tbl(pd.DataFrame(rows).round(4), "a4_length_myth")
    print(t.to_string(index=False))

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]; x = np.arange(2); w = 0.34
    sp = t["spearman_raw"].values; psp = t["partial_spearman_ctrl_size"].values
    ax.bar(x - w / 2, sp, w, label="raw Spearman", color="#C44E52")
    ax.bar(x + w / 2, psp, w, label="규모 통제 부분 Spearman", color="#4C72B0")
    for i in range(2):
        ax.text(i - w / 2, sp[i] + 0.01, f"{sp[i]:.2f}", ha="center", fontsize=9)
        ax.text(i + w / 2, psp[i] + 0.01, f"{psp[i]:.2f}", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(t["length_def"], fontsize=9)
    ax.set_ylim(0, max(sp) * 1.2); ax.set_ylabel("등급과의 상관")
    ax.set_title("'분량↔등급' 상관: 규모 통제 시 급감", fontsize=11); ax.legend(fontsize=8)

    ax = axes[1]
    pct = t["pct_via_size"].values * 100
    ax.bar(x, pct, 0.5, color="#8172B3")
    for i in range(2):
        ax.text(i, pct[i] + 1, f"{pct[i]:.0f}%", ha="center", fontsize=10)
    ax.set_xticks(x); ax.set_xticklabels(t["length_def"], fontsize=9)
    ax.set_ylabel("분량→등급 연관 중 규모 경유 비율 (%)")
    ax.set_title("분량 효과의 대부분이 '규모'를 경유", fontsize=11)
    fig.suptitle("선행연구의 '보고서 길이=ESG 우수' 통념 반박 — 길이는 규모의 대리", fontsize=12)
    fig.tight_layout(); savefig("a4_length_myth")


# ============================================================ 분석 5: 산업 효과 정밀화
def a5(m):
    print("\n[분석 5] 산업 효과 정밀화 — 산업이 등급의 주요 결정요인")
    # (a) 산업 프로파일
    prof = m.groupby("sector").agg(
        n=("doc_id", "size"), mean_grade=(INTEG_GRADE, "mean"),
        mean_log_assets=("log_assets", "mean"), mean_log_core_len=("log_core_doc_len", "mean"),
        **{f"mean_{c}": (c, "mean") for c in TEXT_COLS}).reset_index().sort_values("mean_grade", ascending=False)
    tbl(prof.round(3), "a5_industry_profile")
    print(prof[["sector", "n", "mean_grade", "mean_log_assets", "mean_log_core_len"]].round(2).to_string(index=False))

    # (b) 산업-only 설명력 + 편차(sum-to-zero) 코딩 효과
    ro = fit_ols(m, INTEG_GRADE, SECTOR_DUMMIES); rl = fit_ordered(m, INTEG_GRADE, SECTOR_DUMMIES)
    print(f"  산업-only: OLS R²={ro['r2']:.3f}, McFadden={rl['mcfadden']:.3f}")
    # 편차코딩: 각 sector 평균 - 전체평균, 단순 OLS(grade ~ C(sector), sum) 대신 그룹평균 차이로 직접 산출 + 유의성
    grand = m[INTEG_GRADE].mean()
    eff_rows = []
    for sec in sorted(m["sector"].unique()):
        d = m.assign(_in=(m["sector"] == sec).astype(int))
        r = fit_ols(d, INTEG_GRADE, ["_in"])      # in-sector vs rest 평균차 (유의성 참고용)
        eff_rows.append(dict(sector=sec, n=int((m["sector"] == sec).sum()),
                             mean_grade=m.loc[m.sector == sec, INTEG_GRADE].mean(),
                             dev_from_grand=m.loc[m.sector == sec, INTEG_GRADE].mean() - grand,
                             vs_rest_coef=r["params"]["_in"], vs_rest_p=r["pvals"]["_in"]))
    edf = pd.DataFrame(eff_rows).sort_values("dev_from_grand", ascending=False)
    edf["sig"] = edf["vs_rest_p"].map(sig_stars)
    tbl(edf.round(4), "a5_industry_effects")

    fig, ax = plt.subplots(figsize=(9.5, 5))
    colors = ["#C44E52" if v > 0 else "#4C72B0" for v in edf["dev_from_grand"]]
    bars = ax.barh(range(len(edf)), edf["dev_from_grand"], color=colors)
    ax.set_yticks(range(len(edf)))
    ax.set_yticklabels([f"{r.sector} (n={r.n})" for r in edf.itertuples()], fontsize=9)
    ax.invert_yaxis(); ax.axvline(0, color="k", lw=0.7)
    for b, r in zip(bars, edf.itertuples()):
        ax.text(b.get_width() + (0.03 if b.get_width() >= 0 else -0.03), b.get_y() + b.get_height() / 2,
                f"{r.dev_from_grand:+.2f}{r.sig}", va="center",
                ha="left" if b.get_width() >= 0 else "right", fontsize=8)
    ax.set_xlim(edf["dev_from_grand"].min() - 0.5, edf["dev_from_grand"].max() + 0.5)
    ax.set_xlabel("전체 평균등급 대비 편차 (sum-to-zero)")
    ax.set_title(f"산업별 ESG 등급 편차 (전체평균 {grand:.2f}) — 산업이 등급을 크게 가름\n산업-only McFadden={rl['mcfadden']:.3f}", fontsize=11)
    fig.tight_layout(); savefig("a5_industry_effects")

    # (c) 산업 within 텍스트 효과: 자기차원 부분ρ (산업+길이+규모 통제)
    wr = []
    for rk in REPR_ORDER:
        for dim, raw, z, gcol in own(rk):
            rho_full = partial_spearman(m, raw, gcol, [LEN_Z, SIZE_Z] + SECTOR_DUMMIES)
            rho_ind = partial_spearman(m, raw, gcol, SECTOR_DUMMIES)
            wr.append(dict(repr=rk, label=REPRS[rk]["label"], dim=dim,
                           partial_rho_industry_only=rho_ind,
                           partial_rho_industry_len_size=rho_full))
    tbl(pd.DataFrame(wr).round(3), "a5_within_industry_text")
    print("  산업 within 자기차원 부분ρ(산업+길이+규모 통제):")
    for rk in REPR_ORDER:
        s = [d for d in wr if d["repr"] == rk]
        print("   ", REPRS[rk]["label"], {d["dim"]: round(d["partial_rho_industry_len_size"], 3) for d in s})


# ============================================================ 분석 6: 약신호 정밀도 (부트스트랩·순열)
def _boot_perm(m, xcol, ycol, ctrl, n_boot=5000, n_perm=10000, seed=20260602, group="stock_code"):
    rng = np.random.default_rng(seed)
    obs = partial_spearman(m, xcol, ycol, ctrl)
    idx = np.arange(len(m))
    # row bootstrap
    rb = []
    for _ in range(n_boot):
        sub = m.iloc[rng.choice(idx, len(idx), replace=True)]
        rb.append(partial_spearman(sub, xcol, ycol, ctrl))
    # cluster (firm) bootstrap
    groups = m[group].values
    uniq = np.array(sorted(m[group].unique()))
    gmap = {g: np.where(groups == g)[0] for g in uniq}
    cb = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, len(uniq), replace=True)
        sub = m.iloc[np.concatenate([gmap[g] for g in pick])]
        cb.append(partial_spearman(sub, xcol, ycol, ctrl))
    # permutation: rank-residualize, permute one residual
    rx = _resid(m[xcol].rank().to_numpy(float), m[ctrl].rank().to_numpy(float)) if ctrl else m[xcol].rank().to_numpy(float)
    ry = _resid(m[ycol].rank().to_numpy(float), m[ctrl].rank().to_numpy(float)) if ctrl else m[ycol].rank().to_numpy(float)
    obs_r = pearsonr(rx, ry)[0]
    cnt = 0
    for _ in range(n_perm):
        if abs(pearsonr(rx, rng.permutation(ry))[0]) >= abs(obs_r):
            cnt += 1
    perm_p = (1 + cnt) / (n_perm + 1)
    return dict(obs=obs, row_lo=np.percentile(rb, 2.5), row_hi=np.percentile(rb, 97.5),
                clu_lo=np.percentile(cb, 2.5), clu_hi=np.percentile(cb, 97.5), perm_p=perm_p)


def a6(m):
    print("\n[분석 6] 약신호 정밀도 — 3트랙 핵심 신호 부트스트랩 CI·순열검정 (통일 잣대)")
    ctrl = [LEN_Z, SIZE_Z]
    # (signal, text_col, grade, repr_key, dim) — repr/dim 으로 matched 회귀계수(완전통제) 병기
    signals = [
        ("① seed-G", "tfidf_G", "g_grade", "seed_tfidf", "G"),
        ("① seed-E", "tfidf_E", "e_grade", "seed_tfidf", "E"),
        ("② 확장-G", "expanded_tfidf_G", "g_grade", "expanded", "G"),
        ("③ cosine-E", "E_cos", "e_grade", "dense_cos", "E"),
        ("③ supervised-S", "S_sup", "s_grade", "dense_sup", "S"),
        ("③ supervised-E", "E_sup", "e_grade", "dense_sup", "E"),
    ]
    fc = pd.read_csv(f"{DP}/07d_a3_fullcontrol_coef.csv")   # 완전통제 매칭 회귀계수 + 해석적 기업 cluster CI
    fc["sig"] = fc["sig"].fillna("")
    rows = []
    for name, xc, yc, rk, dim in signals:
        r = _boot_perm(m, xc, yc, ctrl)
        fcr = fc[(fc["repr"] == rk) & (fc.dim == dim)].iloc[0]
        firm_excl0 = (r["clu_lo"] > 0 or r["clu_hi"] < 0)
        verdict = ("기업부트 0제외(견고)" if firm_excl0 else
                   "행부트 0제외·기업부트 0포함(경계)" if (r["row_lo"] > 0 or r["row_hi"] < 0) else "0 포함(비유의)")
        rows.append(dict(signal=name, text_col=xc, grade=yc, obs_partial_rho=r["obs"],
                         row_ci_lo=r["row_lo"], row_ci_hi=r["row_hi"],
                         firm_ci_lo=r["clu_lo"], firm_ci_hi=r["clu_hi"], perm_p=r["perm_p"],
                         firm_excl0=firm_excl0,
                         matched_coef=fcr["coef"], matched_p=fcr["p"], matched_sig=fcr["sig"],
                         matched_ci_lo=fcr["ci_low"], matched_ci_hi=fcr["ci_high"],
                         effect="약" if abs(r["obs"]) < 0.2 else "중", verdict=verdict))
        print(f"  {name:>16}: ρ={r['obs']:+.3f} row[{r['row_lo']:+.3f},{r['row_hi']:+.3f}] "
              f"firm[{r['clu_lo']:+.3f},{r['clu_hi']:+.3f}] perm_p={r['perm_p']:.4f} | "
              f"회귀계수={fcr['coef']:+.3f}{fcr['sig']} ({verdict})")
    t = tbl(pd.DataFrame(rows).round(4), "a6_signal_ci")

    fig, ax = plt.subplots(figsize=(9.5, 5))
    y = np.arange(len(t))[::-1]
    for yi, r in zip(y, t.itertuples()):
        ax.plot([r.firm_ci_lo, r.firm_ci_hi], [yi, yi], color="#999", lw=2, zorder=1)
        ax.plot([r.row_ci_lo, r.row_ci_hi], [yi + 0.0, yi + 0.0], color="#4C72B0", lw=5, alpha=0.5, zorder=2)
        ax.scatter([r.obs_partial_rho], [yi], color="#C44E52", s=60, zorder=3)
    ax.axvline(0, color="k", lw=0.8, ls="--")
    ax.set_yticks(y); ax.set_yticklabels(t["signal"], fontsize=9)
    ax.set_xlabel("부분 Spearman ρ (길이+규모 통제)")
    ax.set_title("3트랙 핵심 신호 forest plot — 두꺼운 파랑=행부트 / 회색=기업부트(보수적) / 점=관측\n"
                 "어느 신호도 ρ≈0.15~0.20·CI 넓음 → '유의 ≠ 중요'", fontsize=10)
    fig.tight_layout(); savefig("a6_forest")


# ============================================================ 분석 7: G 차원 종합
def a7(m):
    print("\n[분석 7] G 차원 측정 종합 — 같은 G인데 표현마다 정반대")
    fc = pd.read_csv(f"{DP}/07d_a3_fullcontrol_coef.csv")
    p3 = pd.read_csv(f"{DP}/07d_a3_partial3x3.csv")
    conv = pd.read_csv(f"{DP}/07d_a3_convergence.csv")
    rows = []
    for rk in REPR_ORDER:
        gcoef = fc[(fc["repr"] == rk) & (fc.dim == "G")].iloc[0]
        gpart = p3[(p3["repr"] == rk) & (p3.text_dim == "G") & (p3.grade_dim == "G")]["partial_rho"].iloc[0]
        rows.append(dict(repr=rk, label=REPRS[rk]["label"], g_coef_fullctrl=gcoef["coef"],
                         g_coef_p=gcoef["p"], g_coef_sig=gcoef["sig"], g_partial_rho=gpart))
    g = pd.DataFrame(rows)
    # 트랙 간 G 수렴(seed_tfidf 기준)
    gconv = conv[(conv.dim == "G")][["repr_a", "repr_b", "spearman"]]
    tbl(g.round(4), "a7_g_synthesis")
    tbl(gconv.round(3), "a7_g_convergence")
    print(g[["label", "g_coef_fullctrl", "g_coef_sig", "g_partial_rho"]].to_string(index=False))
    print("  트랙 간 G 수렴:", {f"{r.repr_a[:4]}×{r.repr_b[:4]}": round(r.spearman, 2) for r in gconv.itertuples()})

    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(len(g)); w = 0.36
    ax.bar(x - w / 2, g["g_coef_fullctrl"], w, label="완전통제 후 계수", color="#C44E52")
    ax.bar(x + w / 2, g["g_partial_rho"], w, label="부분ρ(길이+규모)", color="#4C72B0")
    for i, r in g.iterrows():
        ax.text(i - w / 2, r["g_coef_fullctrl"] + 0.01, f"{r['g_coef_fullctrl']:.2f}{r['g_coef_sig']}", ha="center", fontsize=8)
        ax.text(i + w / 2, r["g_partial_rho"] + 0.01, f"{r['g_partial_rho']:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([REPRS[k]["label"] for k in REPR_ORDER], fontsize=9)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_title("G(지배구조) 신호 — TF-IDF만 강건, dense는 약/음, 확장은 경계\n(seed G는 max_df=1.0에서도 0.51** 유지 = vocab 인공물 아님)", fontsize=10)
    ax.set_ylabel("효과크기"); ax.legend(fontsize=8)
    fig.tight_layout(); savefig("a7_g_bars")


ANALYSES = {"a1": a1, "a2": a2, "a3": a3, "a4": a4, "a5": a5, "a6": a6, "a7": a7}

if __name__ == "__main__":
    m = load_synthesis()
    args = sys.argv[1:] or ["all"]
    todo = list(ANALYSES) if args == ["all"] else args
    for a in todo:
        ANALYSES[a](m)
    print("\n완료:", todo)
