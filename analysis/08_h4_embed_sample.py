"""
08_h4_embed_sample.py — H4(Dense 실패 원인) 보조: 문장 단위 앵커 코사인 표본
=============================================================================
용도: "E cosine 상위 문장에 실제로 G/S 문장이 섞이는가?"(차원 누수)를
구체 문장으로 보이기 위한 *예시용* 표본. KURE-v1 CPU 임베딩이 6 sent/s라
전체 175k 문장은 불가(≈8h) → 문서별 층화 표본(~10문장/문서)만 임베딩한다.

가드레일/주의:
  - 결과는 *예시(exploratory)*. 07 v2 정식 화이트닝 파라미터(07_v2_whiten.npz)는
    Colab 산출물이라 로컬에 없으므로, ABTT(d=10)를 *표본에서 근사 추정*해 적용한다.
  - 정식 문서 점수(E_cos/S_cos/G_cos, max 풀링·전체문장)와 정확히 일치하지 않는다.
  - 앵커는 plan/02_anchors.md(연구자 편집본)의 하위차원 문장 27개(E11·S9·G7).
출력: data/processed/08_h4_sentence_cosine_sample.csv
"""
from __future__ import annotations
import re, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/Users/home1/esg-dart-project")
DP = ROOT / "data/processed"
SENT_PARQUET = DP / "07_v2_sentences.parquet"
ANCHOR_MD = ROOT / "plan/02_anchors.md"
OUT = DP / "08_h4_sentence_cosine_sample.csv"

SEED = 20260603
PER_DOC = 10          # 문서당 표본 문장 수(층화)
MIN_CHARS = 20        # 너무 짧은 조각 제외
ABTT_D = 10           # 상위 주성분 제거 차원(07 v2와 동일 d)


def parse_anchors(md_path: Path) -> dict[str, list[str]]:
    """plan/02_anchors.md 의 하위차원 앵커 문장 파싱 → {E:[...], S:[...], G:[...]}."""
    dim = None
    anchors: dict[str, list[str]] = {"E": [], "S": [], "G": []}
    for line in md_path.read_text(encoding="utf-8").splitlines():
        h = line.strip()
        if h.startswith("## 환경 E"):
            dim = "E"; continue
        if h.startswith("## 사회 S"):
            dim = "S"; continue
        if h.startswith("## 지배구조 G"):
            dim = "G"; continue
        if h.startswith("## ") or h.startswith("---"):
            dim = None; continue
        if dim is None:
            continue
        m = re.match(r"^\s{2,}-\s+(.+)$", line)   # 4-space indented sub-bullet = anchor
        if m:
            anchors[dim].append(m.group(1).strip())
    return anchors


def main():
    rng = np.random.default_rng(SEED)

    anchors = parse_anchors(ANCHOR_MD)
    n_anch = {k: len(v) for k, v in anchors.items()}
    print("anchors:", n_anch)
    assert n_anch == {"E": 11, "S": 9, "G": 7}, f"앵커 수 불일치: {n_anch} (E11/S9/G7 기대)"

    # ---- 문서별 층화 표본 ----
    s = pd.read_parquet(SENT_PARQUET)
    rows = []
    for _, r in s.iterrows():
        doc_id = f"{str(r['stock_code']).zfill(6)}_{int(r['fiscal_year'])}"
        sents = [x for x in list(r["sentences"]) if isinstance(x, str) and len(x) >= MIN_CHARS]
        if not sents:
            continue
        k = min(PER_DOC, len(sents))
        idx = rng.choice(len(sents), size=k, replace=False)
        for i in idx:
            rows.append((doc_id, sents[i]))
    samp = pd.DataFrame(rows, columns=["doc_id", "sentence"]).reset_index(drop=True)
    print("sample sentences:", len(samp), "from", samp.doc_id.nunique(), "docs")

    # ---- 임베딩 ----
    from sentence_transformers import SentenceTransformer
    t0 = time.time()
    model = SentenceTransformer("nlpai-lab/KURE-v1", device="cpu")
    print(f"model load {time.time()-t0:.0f}s")

    anchor_texts = anchors["E"] + anchors["S"] + anchors["G"]
    anchor_dims = ["E"] * 11 + ["S"] * 9 + ["G"] * 7

    t0 = time.time()
    A = model.encode(anchor_texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    Sent = model.encode(samp["sentence"].tolist(), batch_size=32,
                        normalize_embeddings=True, show_progress_bar=True)
    print(f"encode {len(samp)} sents + {len(anchor_texts)} anchors: {time.time()-t0:.0f}s")
    A = np.asarray(A, dtype=np.float64); Sent = np.asarray(Sent, dtype=np.float64)

    # ---- raw 앵커 코사인(화이트닝 전) ----
    def dim_cos(M, anchor_mat):
        sims = M @ anchor_mat.T          # (n_sent, n_anchor)
        out = {}
        for d in ("E", "S", "G"):
            cols = [i for i, dd in enumerate(anchor_dims) if dd == d]
            out[d] = sims[:, cols].max(axis=1)   # 차원 점수 = 그 차원 앵커 max
        return out

    raw = dim_cos(Sent, A)

    # ---- ABTT(d=10) 근사: 표본 문장에서 평균제거 + 상위 d 주성분 제거 → 재정규화 ----
    mu = Sent.mean(axis=0, keepdims=True)
    Sc = Sent - mu
    # 상위 주성분(문장 공분산)
    U, sv, Vt = np.linalg.svd(Sc, full_matrices=False)
    top = Vt[:ABTT_D]                              # (d, 1024)
    def abtt(M):
        Mc = M - mu
        Mc = Mc - (Mc @ top.T) @ top              # 상위 d 성분 제거
        nrm = np.linalg.norm(Mc, axis=1, keepdims=True)
        nrm[nrm == 0] = 1.0
        return Mc / nrm
    Sw = abtt(Sent); Aw = abtt(A)
    wht = dim_cos(Sw, Aw)

    out = samp.copy()
    for d in ("E", "S", "G"):
        out[f"{d}_cos_raw"] = raw[d]
        out[f"{d}_cos"] = wht[d]                  # ABTT 근사(주 분석용)
    out["sent_len"] = out["sentence"].str.len()
    out.to_csv(OUT, index=False)
    print("saved:", OUT, out.shape)
    # 간단 점검: 화이트닝 후 차원 간 분리(앵커 자기 코사인 상위 문장 미리보기)
    for d in ("E", "S", "G"):
        top1 = out.nlargest(1, f"{d}_cos")["sentence"].iloc[0]
        print(f"top {d}: {top1[:70]}")


if __name__ == "__main__":
    main()
