# -*- coding: utf-8 -*-
"""repro_lib — 최종제출 노트북의 '4개 원천(raw) 파일 → 산출물' 재현 코어.

게이트형(auto: 산출물 있으면 로드, 없으면 raw에서 계산) 재현 인프라 + 로컬에서 실제로
실행되는 전처리·seed TF-IDF 계산을 단일 출처로 모은다. 무거운/외부 단계(DART API 수집·
dense KURE-v1 GPU 인코딩·fastText 학습)는 노트북 셀에서 게이트로 감싼다(키/GPU 없으면 캐시).

진짜 원천 4파일:
  data/raw/company_master.csv  — 127사×3년 회사목록 + KCGS 등급(라벨) + 업종 + corp/stock code
  data/raw/CORPCODE.xml        — stock_code(6) → corp_code(8) (DART 수집 키)
  data/raw/seed_dictionary.csv — E/S/G×10 seed 30개
  data/raw/stopwords_ko_esg.txt— 전처리 불용어

로컬 재현 체인(키/GPU 불필요, 본 모듈로 실행·검증 가능):
  data/processed/dart_reports/*.json(수집 산출) → preprocess_reports() → dart_preprocessed.csv
  → build_seed_tfidf() → 05_tfidf_seed_features.parquet  (committed 값 1e-6 내 복원)

전처리 로직 출처 notebooks/03_데이터전처리.ipynb · seed 점수 출처 notebooks/05b_TF_IDF.ipynb.
"""
from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("ESG_ROOT", "/Users/home1/esg-dart-project"))
RAW = ROOT / "data" / "raw"
DP = ROOT / "data" / "processed"
REPORT_DIR = DP / "dart_reports"

# ── 진짜 원천 4파일 ──────────────────────────────────────────────────────────
RAW_FILES = {
    "company_master": RAW / "company_master.csv",   # 회사목록·등급·업종
    "corpcode": RAW / "CORPCODE.xml",               # stock→corp 매핑
    "seed": RAW / "seed_dictionary.csv",            # seed 30개
    "stopwords": RAW / "stopwords_ko_esg.txt",      # 불용어
}


def assert_raw_inputs() -> dict[str, Path]:
    """시작 시 4개 원천 파일 존재를 강제한다(재현의 출발점)."""
    missing = [str(p) for p in RAW_FILES.values() if not p.exists()]
    assert not missing, "원천 파일 없음: " + ", ".join(missing)
    return RAW_FILES


# ── 게이트(auto: 있으면 로드, 없으면 raw에서 계산) ───────────────────────────
def stage(artifact, compute, label, needs=None, loader=None, force=None):
    """단계 실행 게이트.

    artifact 가 있으면 로드한다. 없으면 compute()로 raw에서 생성한다.
    needs(예: 'DART_API_KEY')가 주어졌는데 환경에 없고 산출물도 없으면, 계산 불가를
    안내하고 None을 돌려준다(노트북은 캐시 경로로 계속). force/RUN_FROM_RAW 로 재계산 강제.

    반환: (obj, did_compute: bool)
    """
    artifact = Path(artifact)
    mode = force if force is not None else os.environ.get("RUN_FROM_RAW", "auto")
    loader = loader or (lambda p: pd.read_csv(p))

    want_compute = (mode == "force") or (not artifact.exists())
    if want_compute and needs and not os.environ.get(needs):
        if artifact.exists():
            print(f"[{label}] {needs} 없음 → 캐시 로드: {artifact.name}")
            return loader(artifact), False
        print(f"[{label}] 산출물·{needs} 모두 없음 → 이 단계는 {needs}(+네트워크/GPU)가 있어야 재현됩니다.")
        return None, False

    if want_compute:
        print(f"[{label}] raw에서 계산 → {artifact.name}")
        obj = compute()
        return obj, True

    print(f"[{label}] 캐시 로드: {artifact.name}")
    return loader(artifact), False


# ── 전처리 (notebooks/03 lift): dart_reports/*.json + 불용어 → kiwi_text ──────
SECTION_LABELS = ["II", "IV", "VI", "VIII", "XI"]
CORE_SECTIONS = ["II", "IV", "VI"]
_ROMAN_UNICODE = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹⅺⅻ"
_ROMAN_TOKEN = r"(?:VIII|VII|XII|XI|IV|IX|III|II|VI|V|X|I|viii|vii|xii|xi|iv|ix|iii|ii|vi|v|x|i)"
_ROMAN_NUMBERED_RE = re.compile(rf"(?<![A-Za-z]){_ROMAN_TOKEN}\s*[\.\)]")
_ROMAN_STANDALONE_RE = re.compile(rf"(?<![A-Za-z]){_ROMAN_TOKEN}(?![A-Za-z])")
_KO_BULLET_RE = re.compile(r"\([가-힣]\)|\([0-9]+\)|[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]|[가-힣]\.\s")
_ROMAN_UNICODE_RE = re.compile(rf"[{_ROMAN_UNICODE}]")
_TOKEN_RE = re.compile(r"^[가-힣A-Za-z]+$")
_KEEP_POS_PREFIXES = ("N", "V")
_KEEP_POS_TAGS = {"SL"}
GENERIC_CORPORATE = {
    "회사", "당사", "사업", "내용", "관련", "사항", "기준", "관리", "운영", "활동",
    "실시", "제도", "계획", "현황", "대상", "경우", "통해", "위해", "대한", "대하", "따르",
    "보고", "작성", "연결", "별도", "재무", "매출", "손익", "자산", "부채", "금액", "계약",
    "제품", "시장", "부문", "영업", "생산", "판매", "서비스", "종속", "관계", "변경", "증가", "감소",
    "찬성", "반대", "가결", "선임", "위원", "위원장", "총회", "후보",
}
ROMAN_TOKENS = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"}


def load_stopwords(path=None, *, extend_generic=True, extend_roman=True) -> set[str]:
    """stopwords_ko_esg.txt 로드(NFKC·소문자·주석/공백 제외) + 일반공시어·로마숫자 안전망."""
    path = Path(path or RAW_FILES["stopwords"])
    with path.open("r", encoding="utf-8") as f:
        sw = {
            unicodedata.normalize("NFKC", line.strip()).lower()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        }
    if extend_generic:
        sw |= GENERIC_CORPORATE
    if extend_roman:
        sw |= ROMAN_TOKENS
    return sw


def strip_section_markers(text: str) -> str:
    if not isinstance(text, str) or not text:
        return ""
    text = _ROMAN_UNICODE_RE.sub(" ", text)
    text = _ROMAN_NUMBERED_RE.sub(" ", text)
    text = _ROMAN_STANDALONE_RE.sub(" ", text)
    text = _KO_BULLET_RE.sub(" ", text)
    return text


def _load_report_row(path: Path) -> dict:
    import json
    payload = json.loads(path.read_text(encoding="utf-8"))
    sections = payload.get("sections") or {}
    texts = [sections.get(l).strip() for l in SECTION_LABELS
             if isinstance(sections.get(l), str) and sections.get(l).strip()]
    return {
        "회사이름": payload.get("company_name"),
        "stock_code": str(payload.get("stock_code", "")).zfill(6),
        "fiscal_year": payload.get("fiscal_year"),
        "esg_year": payload.get("esg_year"),
        "status": payload.get("status"),
        "raw_text": "\n\n".join(texts),
    }


def preprocess_reports(report_dir=None, stopwords_path=None, out_csv=None, save=True) -> pd.DataFrame:
    """dart_reports/*.json(II·IV·VI·VIII·XI) + 불용어 → Kiwi 토큰화 → dart_preprocessed.csv.

    notebooks/03_데이터전처리.ipynb 와 동일 로직. 컬럼: 회사이름·esg_year·raw_text·clean_text·kiwi_text.
    """
    from kiwipiepy import Kiwi
    report_dir = Path(report_dir or REPORT_DIR)
    out_csv = Path(out_csv or (DP / "dart_preprocessed.csv"))
    stopwords = load_stopwords(stopwords_path)

    df = pd.DataFrame(_load_report_row(p) for p in sorted(report_dir.glob("*.json")))

    keep_re, ws_re = re.compile(r"[^가-힣A-Za-z0-9\s]+"), re.compile(r"\s+")

    def to_clean(text):
        if not isinstance(text, str) or not text.strip():
            return ""
        text = unicodedata.normalize("NFKC", text)
        text = strip_section_markers(text)
        text = keep_re.sub(" ", text)
        return ws_re.sub(" ", text).strip().lower()

    kiwi = Kiwi()

    def tokens(text):
        if not isinstance(text, str) or not text.strip():
            return []
        text = strip_section_markers(unicodedata.normalize("NFKC", text))
        out = []
        for t in kiwi.tokenize(text):
            w = unicodedata.normalize("NFKC", t.form).lower().strip()
            if len(w) <= 1 or w in stopwords or not _TOKEN_RE.fullmatch(w):
                continue
            if not (t.tag.startswith(_KEEP_POS_PREFIXES) or t.tag in _KEEP_POS_TAGS):
                continue
            out.append(w)
        return out

    df["clean_text"] = df["raw_text"].map(to_clean)
    df["kiwi_text"] = df["raw_text"].map(lambda x: " ".join(tokens(x)))
    out = df[["회사이름", "esg_year", "raw_text", "clean_text", "kiwi_text"]].copy()
    if save:
        out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    return out


def section_lengths(report_dir=None, out_csv=None, save=True) -> pd.DataFrame:
    """dart_reports/*.json → 섹션별 문자수(len_II..) + len_total. 길이통제 = log(II+IV+VI)."""
    import json
    report_dir = Path(report_dir or REPORT_DIR)
    out_csv = Path(out_csv or (DP / "dart_section_lengths.csv"))
    rows = []
    for p in sorted(report_dir.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        sec = d.get("sections") or {}
        r = {"company_name": d.get("company_name"),
             "stock_code": str(d.get("stock_code", "")).zfill(6),
             "fiscal_year": d.get("fiscal_year"), "esg_year": d.get("esg_year"),
             "status": d.get("status")}
        for l in SECTION_LABELS:
            r[f"len_{l}"] = len(sec.get(l) or "")
        r["len_total"] = sum(r[f"len_{l}"] for l in SECTION_LABELS)
        rows.append(r)
    out = pd.DataFrame(rows)
    if save:
        out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    return out


# ── seed TF-IDF (notebooks/05b lift): kiwi_text + seed + master → tfidf_E/S/G ─
ESG_DIMS = ["E", "S", "G"]
TFIDF_MIN_DF, TFIDF_MAX_DF, TFIDF_NORM = 2, 0.95, "l2"
KEY_COLS = ["stock_code", "fiscal_year"]


def _seed_tokenizer(stopwords):
    """05b tokenize_seed_phrase — Kiwi(N/V/SL) + compact/split 형태, 불용어 제거."""
    from kiwipiepy import Kiwi
    kiwi = Kiwi()

    def normalize(w):
        return unicodedata.normalize("NFKC", str(w)).lower().strip()

    def tokenize_phrase(phrase):
        if not isinstance(phrase, str) or not phrase.strip():
            return []
        phrase = normalize(phrase)
        out: set[str] = set()
        compact = re.sub(r"[^가-힣A-Za-z]+", "", phrase)
        if len(compact) > 1 and _TOKEN_RE.fullmatch(compact):
            out.add(compact)
        for part in re.split(r"[^가-힣A-Za-z]+", phrase):
            if len(part) > 1 and _TOKEN_RE.fullmatch(part):
                out.add(part)
        for tok in kiwi.tokenize(phrase):
            w = normalize(tok.form)
            if len(w) <= 1 or not _TOKEN_RE.fullmatch(w):
                continue
            if not (tok.tag.startswith(_KEEP_POS_PREFIXES) or tok.tag in _KEEP_POS_TAGS):
                continue
            out.add(w)
        return sorted(out)

    def candidate_terms(row):
        phrases = [row["seed_term"]]
        if isinstance(row.get("pattern"), str):
            phrases.extend(row["pattern"].split("|"))
        terms = []
        for ph in phrases:
            terms.extend(tokenize_phrase(ph))
        return sorted({t for t in terms if t not in stopwords})

    return candidate_terms


def build_seed_tfidf(preprocessed=None, master=None, seed=None, stopwords_path=None,
                     out_parquet=None, save=True) -> dict:
    """seed TF-IDF 점수(tfidf_E/S/G) 산출. notebooks/05b 설정 정확 복원.

    입력: dart_preprocessed.csv(kiwi_text) + company_master.csv(키·등급) + seed_dictionary.csv
          + stopwords_ko_esg.txt. vocab=40,101 기대. 반환 dict(features, vocab_size, found_by_dim).
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    out_parquet = Path(out_parquet or (DP / "05_tfidf_seed_features.parquet"))

    pre = preprocessed if preprocessed is not None else pd.read_csv(DP / "dart_preprocessed.csv")
    if "회사이름" in pre.columns:
        pre = pre.rename(columns={"회사이름": "company_name"})
    pre = pre.copy()
    pre["company_name"] = pre["company_name"].astype(str).str.strip()
    pre["esg_year"] = pre["esg_year"].astype(int)
    pre["kiwi_text"] = pre["kiwi_text"].astype(str)

    mst = master if master is not None else pd.read_csv(RAW_FILES["company_master"], dtype={"stock_code": "string"})
    mst = mst.copy()
    mst["company_name"] = mst["company_name"].astype(str).str.strip()
    mst["stock_code"] = mst["stock_code"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(6)
    mst["fiscal_year"] = mst["fiscal_year"].astype(int)
    mst["esg_year"] = mst["esg_year"].astype(int)

    mkey = ["company_name", "stock_code", "fiscal_year", "esg_year",
            "esg_grade", "e_grade", "s_grade", "g_grade"]
    corpus = pre.merge(mst[mkey], on=["company_name", "esg_year"], how="left",
                       validate="one_to_one", indicator=True)
    assert (corpus["_merge"] == "both").all(), "company_master 키 복원 실패"
    corpus = corpus.drop(columns=["_merge"]).sort_values(KEY_COLS).reset_index(drop=True)

    vec = TfidfVectorizer(tokenizer=str.split, token_pattern=None, preprocessor=None,
                          lowercase=False, norm=TFIDF_NORM, sublinear_tf=False,
                          min_df=TFIDF_MIN_DF, max_df=TFIDF_MAX_DF)
    X = vec.fit_transform(corpus["kiwi_text"].tolist())
    vocab_to_idx = {t: i for i, t in enumerate(vec.get_feature_names_out())}

    sd = seed if seed is not None else pd.read_csv(RAW_FILES["seed"])
    stopwords = load_stopwords(stopwords_path)
    cand = _seed_tokenizer(stopwords)
    sd = sd.copy()
    sd["candidate_terms"] = sd.apply(cand, axis=1)
    sd["found_terms"] = sd["candidate_terms"].map(lambda ts: [t for t in ts if t in vocab_to_idx])
    found_by_dim = {
        d: sorted({t for ts in sd.loc[sd["dimension"] == d, "found_terms"] for t in ts})
        for d in ESG_DIMS
    }

    def sum_cols(words):
        cols = [vocab_to_idx[w] for w in sorted(set(words)) if w in vocab_to_idx]
        if not cols:
            return np.zeros(X.shape[0])
        return np.asarray(X[:, cols].sum(axis=1)).ravel()

    scores = {d: sum_cols(found_by_dim[d]) for d in ESG_DIMS}
    features = pd.DataFrame({
        "company_name": corpus["company_name"], "stock_code": corpus["stock_code"],
        "fiscal_year": corpus["fiscal_year"], "esg_year": corpus["esg_year"],
        "tfidf_E": scores["E"], "tfidf_S": scores["S"], "tfidf_G": scores["G"],
    })
    if save:
        features.to_parquet(out_parquet, index=False)
    return {"features": features, "vocab_size": X.shape[1], "found_by_dim": found_by_dim,
            "seed_match": sd[["dimension", "seed_term", "found_terms"]]}
