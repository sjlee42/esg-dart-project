"""엔진 신뢰성 검증: 내 회귀/부분상관 엔진이 committed 05b 수치를 복원하는가."""
import numpy as np, pandas as pd
from synth_lib import (load_synthesis, fit_ordered, partial_spearman, partial_pearson,
                       _resid, LEN_Z, SIZE_Z, SECTOR_DUMMIES, YEAR_DUMMIES, DP)
from scipy.stats import spearmanr, pearsonr

m = load_synthesis(rebuild=True)
print("=== synthesis table ===", m.shape)

# z-score 일관성 (dense 의 기존 _z 가 ddof=0 인가)
for c in ["E_cos", "log_assets"]:
    z = (m[c]-m[c].mean())/m[c].std(ddof=0)
    print(f"  z-check {c}: max|Δ| vs committed _z = {np.abs(z - m[c+'_z']).max():.2e}")

# ---------------------------------------------------------------- 1) matched ordered logit 복원
specs = {
    "01_text_only":  [],
    "02_add_length": [LEN_Z],
    "03_add_size":   [LEN_Z, SIZE_Z],
    "04_add_industry": [LEN_Z, SIZE_Z] + SECTOR_DUMMIES,
    "05_add_year":   [LEN_Z, SIZE_Z] + SECTOR_DUMMIES + YEAR_DUMMIES,
}
dim2 = {"E": ("tfidf_E_z", "e_grade"), "S": ("tfidf_S_z", "s_grade"), "G": ("tfidf_G_z", "g_grade")}
comm = pd.read_csv(f"{DP}/05b_tfidf_seed_matched_ordered_logit_summary.csv")

print("\n=== matched ordered logit: 내 엔진 vs committed (text_score 계수) ===")
print(f"{'dim':>3} {'spec':>14} {'mine':>9} {'committed':>10} {'Δ':>9}")
for dim, (xz, yc) in dim2.items():
    for spec, ctrl in specs.items():
        r = fit_ordered(m, yc, [xz] + ctrl)
        mine = r["params"][xz]
        cc = comm[(comm.dimension == dim) & (comm.spec == spec) & (comm.term == xz)]
        cval = float(cc.coef.iloc[0]) if len(cc) else np.nan
        flag = "  <-- final" if spec == "05_add_year" else ""
        print(f"{dim:>3} {spec:>14} {mine:>9.4f} {cval:>10.4f} {mine-cval:>9.2e}{flag}")

# ---------------------------------------------------------------- 2) integrated ordered logit 복원
print("\n=== integrated ordered logit final(05): 내 엔진 vs committed ===")
ci = pd.read_csv(f"{DP}/05b_tfidf_seed_integrated_ordered_logit_summary.csv")
xall = ["tfidf_E_z", "tfidf_S_z", "tfidf_G_z", LEN_Z, SIZE_Z] + SECTOR_DUMMIES + YEAR_DUMMIES
r = fit_ordered(m, "esg_grade_num", xall)
for t in ["tfidf_E_z", "tfidf_S_z", "tfidf_G_z", LEN_Z, SIZE_Z]:
    cc = ci[(ci.spec == "05_add_year") & (ci.term == t)]
    cval = float(cc.coef.iloc[0]) if len(cc) else np.nan
    print(f"  {t:>20} mine={r['params'][t]:>8.4f} (p={r['pvals'][t]:.3f})  committed={cval:>8.4f}  Δ={r['params'][t]-cval:.2e}")

# ---------------------------------------------------------------- 3) partial spearman 방법 선택
print("\n=== partial spearman (len+size) — 방법별 vs committed obs ===")
target = {"E": 0.1983, "S": 0.0950, "G": 0.1726}
ctrl_raw = ["log_core_doc_len", "log_assets"]
ctrl_z   = [LEN_Z, SIZE_Z]
for dim, (xz, yc) in dim2.items():
    xr = f"tfidf_{dim}"
    # A: rank-partial (lib 기본)  B: raw residual then spearman  C: rank vars, raw control
    A = partial_spearman(m, xr, yc, ctrl_z)
    rx = _resid(m[xr].to_numpy(float), m[ctrl_raw].to_numpy(float))
    ry = _resid(m[yc].to_numpy(float), m[ctrl_raw].to_numpy(float))
    B = float(spearmanr(rx, ry).statistic)
    print(f"  {dim}: rank-partial(A)={A:+.4f}  raw-resid-spearman(B)={B:+.4f}  committed={target[dim]:+.4f}")

print("\n검증 끝. (Δ가 ~1e-2 이내면 신뢰)")
