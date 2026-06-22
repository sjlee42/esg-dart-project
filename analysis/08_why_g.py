"""
08_why_g.py — "왜 G만 남았는가?" 4가지 가설 검증 엔진
=====================================================
3트랙 종합(07d) 결과에서 seed TF-IDF는 완전통제 후 *지배구조(G)* 만 강건하게
살아남았다(매칭 0.38**). 이 엔진은 그 이유를 4개 경쟁가설로 분해한다.

  H1 KCGS 평가구조  : 통합등급이 구조적으로 G에 유리한가? (E/S/G 분리 등급으로 3×4 교차회귀)
  H2 G 측정가능성   : G는 텍스트로 재기 쉬운 차원인가? (상/하위 G기업 문장·키워드)
  H3 사전 품질      : E/S 사전이 부실해서 G만 남은 건가? (per-term df·tfidf·등급상관)
  H4 Dense 실패     : 임베딩이 왜 TF-IDF만 못한가? (차원분리·수렴·길이·문장누수)

규약(synth_lib 재사용): 순서형=OrderedModel(logit)+기업 cluster SE, z-score ddof=0,
부분 Spearman=순위 잔차화, 완전통제={길이,규모,업종,연도}. 인과 아님(연관/예측).
TF-IDF 재구성은 committed parquet 와 1e-16 수준 일치 검증됨.
"""
from __future__ import annotations
import re, sys, unicodedata, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, mannwhitneyu

ROOT = Path("/Users/home1/esg-dart-project")
DP = ROOT / "data/processed"
FIG = ROOT / "reports/figures"
sys.path.insert(0, str(ROOT / "analysis"))
import synth_lib as S  # noqa: E402  (회귀 엔진·통제블록·통일 규약 재사용)

warnings.filterwarnings("ignore")

LEN_Z, SIZE_Z = S.LEN_Z, S.SIZE_Z
CTRL_LS = [LEN_Z, SIZE_Z]                 # 부분상관 통제 = 길이+규모
CTRL_FULL = S.CTRL_FULL                   # 완전통제 = 길이+규모+업종+연도
GRADE_NUM = {"E": "e_grade", "S": "s_grade", "G": "g_grade", "ESG": "esg_grade_num"}
TFIDF = {"E": "tfidf_E", "S": "tfidf_S", "G": "tfidf_G"}

# ── G 키워드 2분류 (per-term 분석 결과 반영, 08_h3_perterm 근거):
#   DRIVER  = tfidf_G 를 *실제로* 끄는 선택적 어휘(윤리·준법/컴플라이언스·부패방지·의결권) — vocab 잔존·등급상관 높음
#   BOILER  = 거의 모든 보고서에 등장(이사회·사외이사·주주)해 max_df=0.95 로 vocab 에서 제거된 보일러플레이트
#            (감사위원회는 vocab 에 있으나 df 2.4%·ρ0.04 로 사실상 기여 없음 → 보일러/유명무실)
G_DRIVER = {  # 선택적 컴플라이언스·윤리 어휘 (per-term: 컴플라이언스 ρ.43·윤리 .33·부패방지 .33)
    "윤리경영": r"윤리경영|윤리규범|윤리강령|행동강령|윤리헌장|윤리서약",
    "준법·컴플라이언스": r"준법|컴플라이언스|compliance",
    "부패방지": r"부패방지|반부패|뇌물|청렴|부정청탁|청탁금지",
}
G_BOILER = {  # 의무·절차적 거버넌스 (거의 모든 보고서·max_df 제거 또는 df<5%·ρ≈0)
    "이사회": r"이사회", "사외이사": r"사외이사", "감사위원회": r"감사위원",
    "주주총회·의결권": r"주주총회|의결권",
}
# 광의 G(상/하위 표 표시용)
G_KEYWORDS = {**G_DRIVER, **G_BOILER}
E_KEYWORDS = {"온실가스": r"온실가스|탄소|배출", "재생에너지": r"재생에너지|신재생|태양광|풍력",
              "폐기물": r"폐기물|재활용|자원순환", "환경경영": r"환경경영|환경경영시스템"}
S_KEYWORDS = {"산업안전": r"산업안전|중대재해|안전보건|산업재해", "인권": r"인권",
              "노동": r"노동조합|노사|근로자", "협력사": r"협력사|동반성장|상생"}


# ═══════════════════════════════════════════════════════════ load + TF-IDF 재구성
def load_synth() -> pd.DataFrame:
    df = pd.read_csv(S.SYNTH_TBL, dtype={"stock_code_str": str})
    return df


def build_tfidf():
    """committed 와 일치하는 TF-IDF 행렬·vocab·차원별 seed term 복원."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from kiwipiepy import Kiwi
    pp = pd.read_csv(DP / "dart_preprocessed.csv")[["회사이름", "esg_year", "kiwi_text"]] \
        .rename(columns={"회사이름": "company_name"})
    feat = pd.read_parquet(DP / "05_tfidf_seed_features.parquet")
    keys = feat[["company_name", "esg_year", "stock_code", "fiscal_year"]].copy()
    pp = pp.merge(keys, on=["company_name", "esg_year"], how="left", validate="1:1")
    pp["doc_id"] = pp["stock_code"].astype(str).str.zfill(6) + "_" + pp["fiscal_year"].astype(int).astype(str)

    vec = TfidfVectorizer(tokenizer=str.split, token_pattern=None, preprocessor=None,
                          lowercase=False, norm="l2", sublinear_tf=False, min_df=2, max_df=0.95)
    X = vec.fit_transform(pp["kiwi_text"].fillna("").tolist())
    vocab = vec.get_feature_names_out(); v2i = {t: i for i, t in enumerate(vocab)}

    sw = set()
    for line in (ROOT / "data/raw/stopwords_ko_esg.txt").read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            sw.add(unicodedata.normalize("NFKC", s).lower())
    sw |= {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"}
    kiwi = Kiwi(); TOK = re.compile(r"^[가-힣A-Za-z]+$")

    def norm(w): return unicodedata.normalize("NFKC", str(w)).lower().strip()

    def tok(ph):
        if not isinstance(ph, str) or not ph.strip():
            return []
        ph = norm(ph); out = set()
        comp = re.sub(r"[^가-힣A-Za-z]+", "", ph)
        if len(comp) > 1 and TOK.fullmatch(comp):
            out.add(comp)
        for part in re.split(r"[^가-힣A-Za-z]+", ph):
            if len(part) > 1 and TOK.fullmatch(part):
                out.add(part)
        for t in kiwi.tokenize(ph):
            w = norm(t.form)
            if len(w) > 1 and TOK.fullmatch(w) and (t.tag.startswith(("N", "V")) or t.tag == "SL"):
                out.add(w)
        return sorted(out)

    seed = pd.read_csv(ROOT / "data/raw/seed_dictionary.csv")

    def cand(row):
        ph = [row["seed_term"]] + (row["pattern"].split("|") if isinstance(row.get("pattern"), str) else [])
        terms = []
        for p in ph:
            terms += tok(p)
        return sorted({t for t in terms if t not in sw})

    seed["cand"] = seed.apply(cand, axis=1)
    # seed_term -> 매칭된 vocab terms (차원·seed 라벨 유지)
    term_rows = []
    found = {"E": [], "S": [], "G": []}
    for _, r in seed.iterrows():
        for t in r["cand"]:
            if t in v2i:
                found[r["dimension"]].append(t)
                term_rows.append({"dimension": r["dimension"], "seed_term": r["seed_term"], "vocab_term": t})
    found = {d: sorted(set(v)) for d, v in found.items()}
    term_map = pd.DataFrame(term_rows).drop_duplicates(["dimension", "vocab_term"])
    return dict(X=X, vocab=vocab, v2i=v2i, found=found, term_map=term_map, keys=pp[["doc_id", "company_name"]])


# ═══════════════════════════════════════════════════════════ H1 — KCGS 평가구조
def h1(df: pd.DataFrame):
    dims, grades = ["E", "S", "G"], ["E", "S", "G", "ESG"]
    raw = pd.DataFrame(index=dims, columns=grades, dtype=float)
    part = pd.DataFrame(index=dims, columns=grades, dtype=float)
    coef = pd.DataFrame(index=dims, columns=grades, dtype=float)
    pval = pd.DataFrame(index=dims, columns=grades, dtype=float)
    for d in dims:
        tx = TFIDF[d]; txz = tx + "_z"
        for g in grades:
            gc = GRADE_NUM[g]
            raw.loc[d, g] = spearmanr(df[tx], df[gc]).statistic
            part.loc[d, g] = S.partial_spearman(df, tx, gc, CTRL_LS)
            r = S.fit_ordered(df, gc, [txz] + CTRL_FULL)
            coef.loc[d, g] = r["params"][txz]; pval.loc[d, g] = r["pvals"][txz]

    # ESG 총점이 어느 하위등급에 실리나 (KCGS 구조 직접 검정)
    sub = df[["e_grade", "s_grade", "g_grade"]].apply(S.zscore)
    sub.columns = ["e_z", "s_z", "g_z"]
    dec_df = pd.concat([df[["esg_grade_num", "stock_code"]], sub], axis=1)
    ols = S.fit_ols(dec_df, "esg_grade_num", ["e_z", "s_z", "g_z"])
    decomp = pd.DataFrame({
        "sub_grade": ["E", "S", "G"],
        "corr_with_ESG": [spearmanr(df[c], df["esg_grade_num"]).statistic for c in ["e_grade", "s_grade", "g_grade"]],
        "ols_beta_std": [ols["params"][c] for c in ["e_z", "s_z", "g_z"]],
        "ols_p": [ols["pvals"][c] for c in ["e_z", "s_z", "g_z"]],
    })
    return dict(raw=raw, partial=part, coef=coef, pval=pval, decomp=decomp, decomp_r2=ols["r2"])


# ═══════════════════════════════════════════════════════════ H2 — G 측정가능성
def _count_kw(sent: str, patterns: dict) -> list[str]:
    return [name for name, pat in patterns.items() if re.search(pat, sent)]


def _density(ss: list[str], patterns: dict) -> tuple[int, float]:
    """문장 리스트에서 패턴군에 해당하는 문장 수와 100문장당 밀도."""
    n = sum(1 for s in ss if any(re.search(p, s) for p in patterns.values()))
    return n, (100.0 * n / len(ss) if ss else 0.0)


def h2(df: pd.DataFrame, tf: dict, n_extreme: int = 10):
    sents = pd.read_parquet(DP / "07_v2_sentences.parquet")
    sents["doc_id"] = sents["stock_code"].astype(str).str.zfill(6) + "_" + sents["fiscal_year"].astype(int).astype(str)
    sent_by_doc = {d: [x for x in arr if isinstance(x, str)] for d, arr in zip(sents["doc_id"], sents["sentences"])}
    cname = dict(zip(tf["keys"]["doc_id"], tf["keys"]["company_name"]))

    # ── (1) 전체 381 문서에서 DRIVER/BOILER 밀도 계산 → tfidf_G 와의 상관 ──
    drv_den, boi_den, nsent = [], [], []
    for did in df["doc_id"]:
        ss = sent_by_doc.get(did, [])
        drv_den.append(_density(ss, G_DRIVER)[1])
        boi_den.append(_density(ss, G_BOILER)[1])
        nsent.append(len(ss))
    df = df.copy()
    df["g_driver_density"], df["g_boiler_density"], df["n_sent"] = drv_den, boi_den, nsent
    corr = pd.DataFrame({
        "keyword_group": ["DRIVER(윤리·준법·컴플라이언스·부패방지)", "BOILERPLATE(이사회·사외이사·감사위원·주주총회)"],
        "rho_with_tfidf_G": [spearmanr(df["tfidf_G"], df["g_driver_density"]).statistic,
                             spearmanr(df["tfidf_G"], df["g_boiler_density"]).statistic],
        "rho_with_g_grade": [spearmanr(df["g_driver_density"], df["g_grade"]).statistic,
                             spearmanr(df["g_boiler_density"], df["g_grade"]).statistic],
    }).round(3)

    # ── (2) 상/하위 10 기업 표 + 대표 문장 ──
    ranked = df.sort_values("tfidf_G", ascending=False).reset_index(drop=True)
    top = ranked.head(n_extreme).assign(grp="상위10(tfidf_G)")
    bot = ranked.tail(n_extreme).assign(grp="하위10(tfidf_G)")
    rows = []
    for grp_df in (top, bot):
        for _, r in grp_df.iterrows():
            did = r["doc_id"]; ss = sent_by_doc.get(did, [])
            drv_sents = [(_count_kw(s, G_DRIVER), s) for s in ss]
            drv_sents = [(kw, s) for kw, s in drv_sents if kw]
            rep = sorted(drv_sents, key=lambda x: (-len(x[0]), len(x[1])))[:2]
            rep_txt = " ⏐ ".join(s[:88] for _, s in rep) if rep else "(DRIVER G 문장 없음)"
            rows.append({
                "grp": r["grp"], "doc_id": did, "company": cname.get(did, "?"),
                "tfidf_G": round(r["tfidf_G"], 4), "g_grade": int(r["g_grade"]), "n_sent": len(ss),
                "driver_density": round(r["g_driver_density"], 2), "boiler_density": round(r["g_boiler_density"], 2),
                "rep_driver_sentence": rep_txt,
            })
    detail = pd.DataFrame(rows)

    # ── (3) 상위10 vs 하위10 비교 (밀도·등급·길이) ──
    g_top, g_bot = top, bot
    mw_drv = mannwhitneyu(g_top["g_driver_density"], g_bot["g_driver_density"], alternative="greater")
    compare = pd.DataFrame({
        "metric": ["DRIVER 밀도(/100문장)", "BOILER 밀도(/100문장)", "g_grade", "문장 수(길이)"],
        "top10_mean": [g_top["g_driver_density"].mean(), g_top["g_boiler_density"].mean(),
                       g_top["g_grade"].mean(), g_top["n_sent"].mean()],
        "bot10_mean": [g_bot["g_driver_density"].mean(), g_bot["g_boiler_density"].mean(),
                       g_bot["g_grade"].mean(), g_bot["n_sent"].mean()],
    }).round(2)
    return dict(detail=detail, compare=compare, corr=corr, mw_driver_p=float(mw_drv.pvalue))


# ═══════════════════════════════════════════════════════════ H3 — 사전 품질
def h3(df: pd.DataFrame, tf: dict):
    X, v2i, found, term_map = tf["X"], tf["v2i"], tf["found"], tf["term_map"]
    # X 행 순서 = build_tfidf 의 pp 순서 = feat keys 순서. df(synth)와 doc_id 로 정렬 맞추기.
    keys = tf["keys"].reset_index(drop=True)
    order = keys.merge(df[["doc_id", "e_grade", "s_grade", "g_grade", "esg_grade_num"]],
                       on="doc_id", how="left")
    rows = []
    name_by_term = term_map.groupby("vocab_term")["seed_term"].first().to_dict()
    for d in ["E", "S", "G"]:
        gcol = {"E": "e_grade", "S": "s_grade", "G": "g_grade"}[d]
        for t in found[d]:
            col = np.asarray(X[:, v2i[t]].todense()).ravel()
            present = col > 0
            df_count = int(present.sum())
            rho_own = spearmanr(col, order[gcol]).statistic
            rho_esg = spearmanr(col, order["esg_grade_num"]).statistic
            rows.append({
                "dimension": d, "seed_term": name_by_term.get(t, ""), "vocab_term": t,
                "doc_freq": df_count, "doc_freq_pct": round(100 * df_count / len(col), 1),
                "mean_tfidf": round(float(col.mean()), 5),
                "mean_tfidf_present": round(float(col[present].mean()) if df_count else 0.0, 5),
                "rho_own_grade": round(float(rho_own), 3),
                "rho_esg_total": round(float(rho_esg), 3),
            })
    perterm = pd.DataFrame(rows).sort_values(["dimension", "rho_own_grade"], ascending=[True, False])
    # 차원 요약
    summ = perterm.groupby("dimension").agg(
        n_terms=("vocab_term", "size"),
        median_doc_freq_pct=("doc_freq_pct", "median"),
        mean_rho_own=("rho_own_grade", "mean"),
        max_rho_own=("rho_own_grade", "max"),
        share_rho_pos=("rho_own_grade", lambda x: round(100 * (x > 0).mean(), 0)),
    ).reset_index()
    return dict(perterm=perterm, summary=summ)


# ═══════════════════════════════════════════════════════════ H4 — Dense 실패
def h4(df: pd.DataFrame):
    reprs = {"① seed TF-IDF": ["tfidf_E", "tfidf_S", "tfidf_G"],
             "③ dense cosine": ["E_cos", "S_cos", "G_cos"],
             "③ dense supervised": ["E_sup", "S_sup", "G_sup"]}
    sep_rows = []
    for name, cols in reprs.items():
        c = df[cols].corr()
        sep_rows.append({"repr": name, "E-S": c.iloc[0, 1], "E-G": c.iloc[0, 2],
                         "S-G": c.iloc[1, 2], "mean_offdiag": np.mean([c.iloc[0, 1], c.iloc[0, 2], c.iloc[1, 2]])})
    separation = pd.DataFrame(sep_rows).round(3)

    conv_rows = []
    for d, (tc, cc, sc) in {"E": ("tfidf_E", "E_cos", "E_sup"), "S": ("tfidf_S", "S_cos", "S_sup"),
                            "G": ("tfidf_G", "G_cos", "G_sup")}.items():
        conv_rows.append({"dimension": d,
                          "tfidf~cosine": spearmanr(df[tc], df[cc]).statistic,
                          "tfidf~supervised": spearmanr(df[tc], df[sc]).statistic})
    convergence = pd.DataFrame(conv_rows).round(3)

    len_rows = []
    for c in ["tfidf_E", "tfidf_S", "tfidf_G", "E_cos", "S_cos", "G_cos", "E_sup", "S_sup", "G_sup"]:
        len_rows.append({"score": c,
                         "rho_log_core_len": spearmanr(df[c], df["log_core_doc_len"]).statistic,
                         "rho_report_len": spearmanr(df[c], df["report_len"]).statistic})
    length = pd.DataFrame(len_rows).round(3)
    return dict(separation=separation, convergence=convergence, length=length)


def h4_sentence_bleed(top_k: int = 50):
    """배경 임베딩 표본(08_h4_sentence_cosine_sample.csv)에서 차원별 상위 코사인 문장의 누수 측정."""
    p = DP / "08_h4_sentence_cosine_sample.csv"
    if not p.exists():
        return None
    s = pd.read_csv(p)
    rows, examples = [], []
    for d in ["E", "S", "G"]:
        top = s.nlargest(top_k, f"{d}_cos")
        # 각 상위문장에 *다른* 차원 키워드가 들어있나 (누수)
        kwmap = {"E": E_KEYWORDS, "S": S_KEYWORDS, "G": G_KEYWORDS}
        def has(sent, kw):
            return any(re.search(p_, sent) for p_ in kw.values())
        own = kwmap[d]
        others = {k: v for k, v in kwmap.items() if k != d}
        own_hit = top["sentence"].apply(lambda x: has(x, own)).mean()
        other_hit = top["sentence"].apply(lambda x: any(has(x, kw) for kw in others.values())).mean()
        rows.append({"dim": d, "top_k": top_k, "own_kw_share": round(100 * own_hit, 0),
                     "other_dim_kw_share": round(100 * other_hit, 0)})
        for _, r in top.head(3).iterrows():
            tags = [k for k, kw in kwmap.items() if has(r["sentence"], kw)]
            examples.append({"top_dim": d, f"{d}_cos": round(r[f"{d}_cos"], 3),
                             "contains_dims": "".join(tags) or "—", "sentence": r["sentence"][:110]})
    return dict(bleed=pd.DataFrame(rows), examples=pd.DataFrame(examples))


# ═══════════════════════════════════════════════════════════ main
def main():
    df = load_synth()
    print("synth:", df.shape)
    tf = build_tfidf()
    print("tfidf terms E/S/G:", {k: len(v) for k, v in tf["found"].items()})

    r1 = h1(df); r2 = h2(df, tf); r3 = h3(df, tf); r4 = h4(df)

    r1["raw"].to_csv(DP / "08_h1_raw_spearman_3x4.csv")
    r1["partial"].to_csv(DP / "08_h1_partial_spearman_3x4.csv")
    r1["coef"].to_csv(DP / "08_h1_fullcontrol_coef_3x4.csv")
    r1["pval"].to_csv(DP / "08_h1_fullcontrol_pval_3x4.csv")
    r1["decomp"].to_csv(DP / "08_h1_esg_decomposition.csv", index=False)
    r2["detail"].to_csv(DP / "08_h2_company_sentences.csv", index=False)
    r2["compare"].to_csv(DP / "08_h2_top_vs_bottom.csv", index=False)
    r2["corr"].to_csv(DP / "08_h2_keyword_density_corr.csv", index=False)
    r3["perterm"].to_csv(DP / "08_h3_perterm_quality.csv", index=False)
    r3["summary"].to_csv(DP / "08_h3_dimension_summary.csv", index=False)
    r4["separation"].to_csv(DP / "08_h4_dimension_separation.csv", index=False)
    r4["convergence"].to_csv(DP / "08_h4_cross_track_convergence.csv", index=False)
    r4["length"].to_csv(DP / "08_h4_length_sensitivity.csv", index=False)

    print("\n── H1 full-control coef (3×4) ──"); print(r1["coef"].round(3))
    print("\n── H1 ESG decomposition (R²=%.3f) ──" % r1["decomp_r2"]); print(r1["decomp"])
    print("\n── H2 keyword density vs tfidf_G ──"); print(r2["corr"])
    print("\n── H2 top vs bottom G ── (DRIVER MW p=%.4f)" % r2["mw_driver_p"]); print(r2["compare"])
    rb = h4_sentence_bleed()
    if rb is not None:
        rb["bleed"].to_csv(DP / "08_h4_sentence_bleed.csv", index=False)
        rb["examples"].to_csv(DP / "08_h4_sentence_bleed_examples.csv", index=False)
        print("\n── H4 sentence bleed (top-50 per dim) ──"); print(rb["bleed"])
    print("\n── H3 dimension summary ──"); print(r3["summary"])
    print("\n── H4 separation ──"); print(r4["separation"])
    print("\n── H4 convergence ──"); print(r4["convergence"])
    return df, tf, r1, r2, r3, r4


if __name__ == "__main__":
    main()
