"""
10_presentation_figures_v2.py — 발표자료_v2(14장) 핵심 신규 그림 3종
====================================================================
`outputs/발표자료_v2.md` 슬라이드 6·7·8 전용 신규 figure.
**기존 결과 CSV만 시각화**한다 — 재인코딩·재토큰화·무거운 임베딩·회귀
재실행 없음(가드레일). 유일한 계산은 fig06 우측 PC1 막대인데, 이는 이미
published 된 dense supervised E·S·G 점수(07d_synthesis_table.csv)의 주성분
설명비율(종합_기록.md §"③ dense 통합" EVR 92%)을 동일 재현할 뿐 새 모델링이 아님.

출력: reports/presentation_figures/{fig06_meta_survival, fig07_g_coef, fig08b_se_coef}.png + .pdf
폰트: Noto Sans KR→Apple SD Gothic Neo→AppleGothic→NanumGothic 폴백,
      axes.unicode_minus=False (− 글리프 깨짐 방지). 09_presentation_figures.py 와 톤 일치.
색: 생존=채도 높은 파랑+굵게+별, 비유의=옅은 회색(명도·굵기로 구분 — 색각 고려, 빨강/초록 단독 의존 금지).

실행: uv run python analysis/10_presentation_figures_v2.py

슬라이드 매핑
| 셀 | 그림 | 슬라이드 | 데이터 |
|---|---|---|---|
| fig06 | 4×3 생존 그리드 + PC1 92% 막대 | 슬6 메타발견 | 07d_a3_fullcontrol_coef.csv · 07d_a3_meta_survival.csv · 07d_synthesis_table.csv |
| fig07 | G 4법 계수(seed만 생존·단어vs의미 역방향) | 슬7 G 해석 | 07d_a3_fullcontrol_coef.csv · 07d_a7_g_convergence.csv |
| fig08b | S·E 계수(S=supervised만·E=0/4) | 슬8 S·E 해석 | 07d_a3_fullcontrol_coef.csv · 07d_a3_meta_survival.csv |
"""
from __future__ import annotations
import os
import sys
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------- paths
ROOT = "/Users/home1/esg-dart-project"
DP = f"{ROOT}/data/processed"
OUT = f"{ROOT}/reports/presentation_figures"
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------- font
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402


def set_korean_font() -> str:
    candidates = ["Noto Sans KR", "Apple SD Gothic Neo", "AppleGothic", "NanumGothic", "Malgun Gothic"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((c for c in candidates if c in available), "AppleGothic")
    plt.rcParams["font.family"] = chosen
    plt.rcParams["axes.unicode_minus"] = False  # − 글리프 깨짐(□) 방지
    plt.rcParams["figure.dpi"] = 110
    plt.rcParams["savefig.bbox"] = "tight"
    return chosen


FONT = set_korean_font()

# ----------------------------------------------------------------------------- palette (09 와 동일)
P = {
    "dominant": "#34495E",   # 규모/1차 지배 (진남색)
    "control": "#95A5A6",    # 기타 통제 (회색)
    "text_weak": "#BDC3C7",  # 텍스트 신호 약 (옅은 회색)
    "signal": "#2563EB",     # 생존/핵심 신호 (파랑)
    "driver": "#2A9D8F",     # DRIVER/선택적 실질 (teal)
    "boiler": "#C9A227",     # BOILER/의무 형식 (머스터드)
    "nonrobust": "#F4A259",  # 비강건 (옅은 주황)
    "null": "#E3E6E8",       # 비유의/null (옅은 회색)
    "neg": "#E15759",        # 음(−) 관계 강조 (빨강)
    "ink": "#1f2937",
    "muted": "#6b7280",
}

DPI = 200
REPR_ORDER = ["① seed TF-IDF", "② fastText 확장", "③ dense cosine", "③ dense supervised"]


def save_fig(fig, name: str):
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/{name}.{ext}", dpi=DPI, bbox_inches="tight",
                    pad_inches=0.25, facecolor="white")  # pad_inches=잘림 여유
    plt.close(fig)
    print(f"  saved  {name}.png / .pdf")


def _despine(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)
    ax.tick_params(length=0)


def _is_sig(v) -> bool:
    return isinstance(v, str) and v.strip() in ("*", "**", "***")


# ============================================================ fig06 메타발견(생존 그리드 + PC1)
def fig06_meta_survival():
    """슬6: 4종×E·S·G 완전통제 후 생존 그리드 + dense supervised PC1(=공통 축 92%) 막대."""
    c = pd.read_csv(f"{DP}/07d_a3_fullcontrol_coef.csv")
    surv = pd.read_csv(f"{DP}/07d_a3_meta_survival.csv").set_index("dim")
    dims = ["E", "S", "G"]

    # PC1 설명비율 = dense supervised (E_sup,S_sup,G_sup) 주성분 (종합_기록 EVR 92% 재현)
    m = pd.read_csv(f"{DP}/07d_synthesis_table.csv")
    Xs = m[["E_sup", "S_sup", "G_sup"]].to_numpy(float)
    Xs = (Xs - Xs.mean(0)) / Xs.std(0, ddof=0)  # z(모집단 std, 프로젝트 관례)
    sv = np.linalg.svd(Xs, compute_uv=False)
    pc1 = float((sv ** 2)[0] / (sv ** 2).sum())  # ≈ 0.921

    fig = plt.figure(figsize=(13.2, 6.8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.27], wspace=0.10)

    # ── 좌: 생존 그리드
    ax = fig.add_subplot(gs[0])
    ax.set_xlim(0, 3); ax.set_ylim(0, 4); ax.axis("off")
    for ri, rl in enumerate(REPR_ORDER):
        y = 3 - ri
        ax.text(-0.06, y + 0.5, rl, ha="right", va="center", fontsize=14, fontweight="bold", color=P["ink"])
        for di, dl in enumerate(dims):
            row = c[(c.label == rl) & (c.dim == dl)].iloc[0]
            survive = _is_sig(row["sig"])
            fc = P["signal"] if survive else P["null"]
            tc = "white" if survive else P["muted"]
            ax.add_patch(Rectangle((di + 0.04, y + 0.04), 0.92, 0.92, fc=fc, ec="white", lw=3))
            star = row["sig"].strip() if isinstance(row["sig"], str) else ""
            txt = f"{row['coef']:+.2f}{(' ' + star) if star else ''}"
            ax.text(di + 0.5, y + 0.58, txt, ha="center", va="center",
                    fontsize=15, fontweight="bold" if survive else "normal", color=tc)
            ax.text(di + 0.5, y + 0.28, "생존" if survive else "재현 안 됨",
                    ha="center", va="center", fontsize=11, color=tc)
    for di, dl in enumerate(dims):
        ax.text(di + 0.5, 4.12, dl, ha="center", va="center", fontsize=16, fontweight="bold", color=P["ink"])

    band = ("어느 ESG 차원도 표현 4종 중 과반 재현 안 됨    ·    "
            f"E {int(surv.loc['E', 'n_survive_p05'])}/4    ·    "
            f"S {int(surv.loc['S', 'n_survive_p05'])}/4    ·    "
            f"G {int(surv.loc['G', 'n_survive_p05'])}/4")
    ax.text(1.5, -0.42, band, ha="center", va="center", fontsize=13.5, fontweight="bold",
            color=P["ink"], bbox=dict(boxstyle="round,pad=0.5", fc="#eef2ff", ec=P["signal"], lw=1.4))
    ax.text(1.5, 4.66, "표현을 바꾸면 살아남는 차원이 바뀐다  =  안정적 차원 신호 부재",
            ha="center", va="center", fontsize=16.5, fontweight="bold", color=P["ink"])

    # ── 우: PC1 막대(공통 축 하나)
    axp = fig.add_subplot(gs[1])
    axp.bar([0], [pc1 * 100], width=0.62, color=P["dominant"], zorder=3)
    axp.bar([0], [(1 - pc1) * 100], width=0.62, bottom=[pc1 * 100], color=P["null"], zorder=3)
    axp.text(0, pc1 * 100 / 2, f"{pc1 * 100:.0f}%", ha="center", va="center",
             color="white", fontsize=27, fontweight="bold")
    axp.set_ylim(0, 100); axp.set_xlim(-0.75, 0.75)
    axp.set_xticks([]); axp.set_yticks([0, 50, 100])
    axp.tick_params(axis="y", labelsize=10)
    axp.set_ylabel("분산 설명 (%)", fontsize=11)
    axp.set_title("dense supervised\nE·S·G → PC1", fontsize=12.5, fontweight="bold", color=P["ink"], pad=8)
    _despine(axp, keep=("left",))
    axp.annotate("공통 축 하나\n(단일 '공시 충실도')", xy=(0, pc1 * 100), xytext=(0, 112),
                 ha="center", va="bottom", fontsize=10.5, color=P["muted"], annotation_clip=False)

    fig.text(0.5, -0.03,
             "셀 = 완전통제(규모·분량·업종·연도) 후 순서형 로짓 계수 (별=유의 *p<.05 **p<.01)    ·    "
             "PC1 = E_sup·S_sup·G_sup 주성분(EVR)    ·    "
             "출처 07d_a3_fullcontrol_coef.csv · 07d_a3_meta_survival.csv · 07d_synthesis_table.csv",
             ha="center", fontsize=9.5, color=P["muted"])
    save_fig(fig, "fig06_meta_survival")


# ============================================================ fig07 G 계수(단어 vs 의미)
def fig07_g_coef():
    """슬7: G 4법 완전통제 계수 — seed TF-IDF만 생존(0.38**), 단어(+)와 의미(−) 역방향."""
    c = pd.read_csv(f"{DP}/07d_a3_fullcontrol_coef.csv")
    conv = pd.read_csv(f"{DP}/07d_a7_g_convergence.csv")
    rho_sc = float(conv[(conv.repr_a == "seed_tfidf") & (conv.repr_b == "dense_cos")]["spearman"].iloc[0])

    g = c[c.dim == "G"].copy()
    g["ord"] = g.label.apply(REPR_ORDER.index)
    g = g.sort_values("ord").reset_index(drop=True)
    y = np.arange(len(g))[::-1]  # seed 맨 위

    fig, ax = plt.subplots(figsize=(12.0, 6.4))
    for yi, (_, r) in zip(y, g.iterrows()):
        survive = _is_sig(r.sig)
        col = P["signal"] if survive else (P["neg"] if r.coef < 0 else P["text_weak"])
        ax.plot([r.ci_low, r.ci_high], [yi, yi], color=col, lw=3.2 if survive else 2.0,
                zorder=2, solid_capstyle="round")
        ax.scatter(r.coef, yi, color=col, s=160 if survive else 80, zorder=3,
                   edgecolor="white", linewidth=1.4)
        star = r.sig.strip() if isinstance(r.sig, str) else ""
        ax.text(r.ci_high + 0.02, yi, f"β={r.coef:+.2f}{(' ' + star) if star else ''}",
                va="center", ha="left", fontsize=13,
                color=P["ink"] if survive else P["muted"], fontweight="bold" if survive else "normal")
    ax.axvline(0, color=P["muted"], lw=1.0, ls="--", zorder=1)
    ax.set_yticks(y); ax.set_yticklabels(g.label, fontsize=13)
    ax.set_ylim(-0.6, 3.6)
    ax.set_xlim(-0.62, 0.92)
    ax.set_xlabel("G(거버넌스) 계수 β — 완전통제 후 순서형 로짓 (점=계수, 선=95% CI)", fontsize=13)
    _despine(ax, keep=("left",))
    ax.xaxis.grid(True, alpha=0.3); ax.set_axisbelow(True)
    ax.set_title("G에선 '단어를 센' seed TF-IDF만 생존 (β=0.38**) — '의미' 기반은 모두 소멸",
                 fontsize=17, fontweight="bold", color=P["ink"], pad=12)

    # 단어 vs 의미 역방향 콜아웃 (dense cosine 점=y=1 을 가리킴; fastText/β=+0.30 라벨과 분리)
    ax.annotate(f"단어(seed) +0.38**  vs  의미(cosine) {g.loc[2, 'coef']:+.2f}\n"
                f"→ 같은 G인데 역방향 (seed×cosine ρ={rho_sc:+.2f})",
                xy=(g.loc[2, "coef"], 1.0), xytext=(0.20, 1.68),
                fontsize=12.5, color=P["neg"], fontweight="bold", va="center", ha="center",
                arrowprops=dict(arrowstyle="-|>", color=P["neg"], lw=1.7,
                                connectionstyle="arc3,rad=0.20"),
                bbox=dict(boxstyle="round,pad=0.45", fc="#fdecec", ec=P["neg"], lw=1.2))
    fig.text(0.99, 0.01, "출처: 07d_a3_fullcontrol_coef.csv · 07d_a7_g_convergence.csv",
             ha="right", fontsize=9, color=P["muted"])
    save_fig(fig, "fig07_g_coef")


# ============================================================ fig08b S·E 계수(정반대)
def fig08b_se_coef():
    """슬8: S·E 4법 완전통제 계수 — S=dense supervised만 생존(0.55*), E=4종 모두 소멸(0/4)."""
    c = pd.read_csv(f"{DP}/07d_a3_fullcontrol_coef.csv")
    surv = pd.read_csv(f"{DP}/07d_a3_meta_survival.csv").set_index("dim")

    panels = [
        ("S", "S(사회)", "‘학습된 의미’(supervised)에서만 생존", "비지도(cosine)·단어(seed)는 통제 후 소멸\n→ 정답지로 학습해야 잡히는 의미"),
        ("E", "E(환경)", "어느 방식으로도 안정 신호 없음 (0/4)", "통제 전 신호는 규모·분량이 만든 착시\n→ 알맹이는 배출량·감축률 등 정량지표"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.2), sharey=True)
    for ax, (dim, dname, sub, note) in zip(axes, panels):
        d = c[c.dim == dim].copy()
        d["ord"] = d.label.apply(REPR_ORDER.index)
        d = d.sort_values("ord").reset_index(drop=True)
        y = np.arange(len(d))[::-1]
        for yi, (_, r) in zip(y, d.iterrows()):
            survive = _is_sig(r.sig)
            col = P["signal"] if survive else P["text_weak"]
            ax.plot([r.ci_low, r.ci_high], [yi, yi], color=col, lw=3.2 if survive else 2.0,
                    zorder=2, solid_capstyle="round")
            ax.scatter(r.coef, yi, color=col, s=155 if survive else 75, zorder=3,
                       edgecolor="white", linewidth=1.4)
            star = r.sig.strip() if isinstance(r.sig, str) else ""
            ax.text(r.ci_high + 0.03, yi, f"{r.coef:+.2f}{(' ' + star) if star else ''}",
                    va="center", ha="left", fontsize=12.5,
                    color=P["ink"] if survive else P["muted"], fontweight="bold" if survive else "normal")
        ax.axvline(0, color=P["muted"], lw=1.0, ls="--", zorder=1)
        ax.set_yticks(y); ax.set_yticklabels(d.label, fontsize=12.5)
        ax.set_ylim(-0.8, 4.5)  # 상단 여백 = 노트 박스 자리(막대와 겹침 방지)
        ax.set_xlim(-0.5, 1.18)
        n_s = int(surv.loc[dim, "n_survive_p05"])
        ax.set_title(f"{dname}  ·  생존 {n_s}/4\n{sub}", fontsize=13.5, fontweight="bold", color=P["ink"])
        ax.set_xlabel("계수 β (완전통제 후, 95% CI)", fontsize=12)
        _despine(ax, keep=("left",))
        ax.xaxis.grid(True, alpha=0.3); ax.set_axisbelow(True)
        ax.text(0.985, 0.985, note, transform=ax.transAxes, ha="right", va="top",
                fontsize=10.5, color=P["muted"],
                bbox=dict(boxstyle="round,pad=0.4", fc="#f7f7f9", ec=P["control"], lw=1.0))

    fig.suptitle("S와 E는 정반대 — S는 ‘학습된 의미’에서만, E는 어느 방식으로도 안 잡힌다",
                 fontsize=17, fontweight="bold", color=P["ink"], y=1.0)
    fig.text(0.99, 0.005, "출처: 07d_a3_fullcontrol_coef.csv · 07d_a3_meta_survival.csv",
             ha="right", fontsize=9, color=P["muted"])
    fig.tight_layout(rect=[0, 0.02, 1, 0.93])
    save_fig(fig, "fig08b_se_coef")


# ============================================================ main
FIGS = [
    ("fig06_meta_survival", fig06_meta_survival),
    ("fig07_g_coef", fig07_g_coef),
    ("fig08b_se_coef", fig08b_se_coef),
]

if __name__ == "__main__":
    print(f"[10_presentation_figures_v2] font={FONT}  out={OUT}")
    for name, fn in FIGS:
        print(f"- {name}")
        fn()
    print(f"\n완료: {len(FIGS)}개 그림 x (png+pdf) → {OUT}")
