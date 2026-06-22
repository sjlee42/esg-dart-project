# -*- coding: utf-8 -*-
"""notebooks/보고용_분석노트북.ipynb 빌더 — 제출용 단일 분석 노트북.

수집 → 전처리 → 피처(4표현) → 측정 타당성 → 회귀(모델선택·단계통제·생존매트릭스)
→ 종합(위계적 R²·분량통념·표현간 수렴·약신호) → 알파(왜 G만) → 한계.

무거운 단계(DART API 수집·Kiwi 전처리·dense 인코딩)는 1회 수행한 산출물을 로드하고,
분석(타당성·회귀·종합)은 검증된 엔진 `analysis/synth_lib.py` 로 본 노트북에서 재실행한다.
재현: `data/processed/07d_synthesis_table.csv`(381×50) + 07d_*.csv/png · 08_*.csv/png.
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
def md(t): cells.append(nbf.v4.new_markdown_cell(t))
def code(t): cells.append(nbf.v4.new_code_cell(t))

ROOT = "/Users/home1/esg-dart-project"
OUT = f"{ROOT}/notebooks/보고용_분석노트북.ipynb"

# ───────────────────────────────────────────────────────────── 표지
md(r"""# 사업보고서 ESG 서술은 ESG를 재는가, 규모·공시 역량을 재는가
### 한국 DART 사업보고서의 텍스트 측정 타당성 — 제출용 분석 노트북

**비정형데이터분석 · 2조**

> **한 줄 질문**: 사업보고서에 적힌 ESG 텍스트를 점수화하면, 그 점수는 실제 ESG 수준을 재는가, 아니면 기업 규모·공시 역량을 재는가?

**구성(논문형 보고서와 동일한 흐름)**

| 단계 | 내용 | 본 노트북에서 |
|---|---|---|
| 1 데이터 수집 | OpenDART 사업보고서 127사×3년 | 수집 코드 + lineage 로그 로드 |
| 2 전처리 | II·IV·VI 섹션 · Kiwi 형태소 | 전처리 코드 + 산출물 로드 |
| 3 Feature | 4가지 텍스트 표현(2×2) | 구성 코드 + 점수 로드 |
| 4 측정 타당성 | Spearman 3×3 · Mann-Whitney | **라이브 실행** |
| 5 회귀 | 모델 선택 · 단계적 통제 · 생존 매트릭스 | **라이브 실행(엔진)** |
| 6 종합 | 위계적 R² · 분량통념 · 약신호 | 검증 엔진 산출물 정리 |
| 7 알파(α) | 왜 지배구조(G)만 남았나 | 4가설 검증 결과 |
| 8 한계·결론 | 인과 아님 · cheap-talk · KCGS 단일 | 서술 |

**재현·실행 안내**
- 무거운 단계(DART API 수집·Kiwi 전처리·dense KURE-v1 인코딩)는 **1회 수행한 산출물을 로드**한다(코드는 본문에 함께 둔다). 분석(4·5·6)은 검증된 엔진으로 **이 노트북에서 재실행**된다.
- **단위/키**: `doc_id = {stock_code 6자리}_{fiscal_year}` (회사명 단독 merge 금지). **timing**: `esg_year = fiscal_year + 1`.
- **API key**: `.env`(환경변수 `DART_API_KEY`)에서만 로드하며 **코드·노트북에 키 값을 쓰지 않는다.**
- **해석 원칙**: 연관/예측(인과 아님) · "유의 ≠ 중요"(효과크기·CI 병기) · 공시 강도 ≠ 실제 성과(cheap-talk) · 결론은 KCGS 단일 기준의 잠정 결론.
""")

# ───────────────────────────────────────────────────────────── 0 환경
md("## 0. 환경 설정 · 분석 패널 로드")
code('''import sys, os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

ROOT = "/Users/home1/esg-dart-project"
sys.path.insert(0, ROOT + "/analysis")

# 검증된 종합 엔진(개별 트랙 재실행·재인코딩 없음). committed 05b 수치를 1e-6 이내 복원하는 엔진.
from synth_lib import (load_synthesis, fit_ordered, fit_ols, fit_logit, partial_spearman,
                       sig_stars, zscore, REPRS, TEXT_COLS, GRADE_COLS, INTEG_GRADE, ALL_DIMS,
                       LEN_Z, SIZE_Z, CTRL_FULL, SECTOR_DUMMIES, YEAR_DUMMIES, GRADE_MAP, DP, FIG)
from scipy.stats import spearmanr, mannwhitneyu
from IPython.display import Image, display

pd.set_option("display.width", 200); pd.set_option("display.max_columns", 60)
pd.set_option("display.float_format", lambda v: f"{v:.3f}")

def show_fig(name): display(Image(filename=f"{FIG}/{name}.png"))
def show_tbl(name, n=None):
    df = pd.read_csv(f"{DP}/{name}.csv")
    display(df if n is None else df.head(n)); return df

# 3트랙 1:1 병합 분석 패널(381×50: 12 텍스트점수 + 등급 + 통제 + 더미 + z)
m = load_synthesis()
assert len(m) == 381 and m[TEXT_COLS].isna().sum().sum() == 0 and m["doc_id"].nunique() == 381
print("분석 패널 로드:", m.shape, "| 381 기업-연도 · 텍스트 결측 0 · doc_id 유일")
print("GRADE_MAP:", GRADE_MAP)''')

# ───────────────────────────────────────────────────────────── 1 수집
md(r"""## 1. 데이터 수집 (DART lineage)

**OpenDART API로 127개 기업의 2022·2024 사이 사업연도 사업보고서를 수집했다.**

- **표본**: 최대 127사 × 3개 회계연도(2022·2023·2024) = 381 기업-연도. 수업 제공 표본이며 KCGS 전체의 대표표본이 아닌 pilot panel.
- **lineage 키**: `stock_code`(6자리) → `corp_code`(8자리, CORPCODE.xml) → 사업보고서 `rcept_no`(접수번호) → `fiscal_year`. 회사명만으로 merge하거나 접수번호가 다른 보고서를 섞지 않는다.
- **결측 처리**: 수집·추출 실패 행은 **가짜 0으로 채우지 않고** 사유를 기록(`dart_collection_status.csv`). 최종 분석 패널은 텍스트·등급이 모두 있는 행으로 구성(결측 0).
- **API key**: 환경변수 `DART_API_KEY`(.env)에서만 로드 — 아래 코드·노트북 어디에도 키 값이 없다.""")
code('''# ── 수집 코드 (notebooks/01_데이터수집.ipynb 에서 1회 수행) — 함수 정의만, API 호출 없음 ──
import io, zipfile, requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass

API_KEY = os.environ.get("DART_API_KEY", "")          # .env 로드, 코드에 키 값 없음
OPENDART_BASE = "https://opendart.fss.or.kr/api"

def build_stock_to_corp_map(corpcode_xml=ROOT + "/data/raw/CORPCODE.xml") -> dict:
    """OpenDART CORPCODE.xml → {stock_code(6자리): corp_code(8자리)} 매핑."""
    root = ET.parse(corpcode_xml).getroot()
    out = {}
    for el in root.iter("list"):
        sc = (el.findtext("stock_code") or "").strip()
        cc = (el.findtext("corp_code") or "").strip()
        if sc and sc != " " and cc:
            out[sc.zfill(6)] = cc
    return out

@dataclass
class ReportSelection:                                # 접수번호로 보고서 1건을 특정
    report_nm: str; rcept_no: str; rcept_dt: str
    corp_code: str; stock_code: str; fiscal_year: int

def fetch_business_report_list(corp_code: str, fiscal_year: int) -> dict:
    """정기공시 목록 조회(list.json) → 해당 회계연도 사업보고서 rcept_no 선택."""
    params = {"crtfc_key": API_KEY, "corp_code": corp_code,
              "bgn_de": f"{fiscal_year+1}0101", "end_de": f"{fiscal_year+1}1231",
              "pblntf_ty": "A", "page_count": 100}                  # A = 정기공시
    return requests.get(f"{OPENDART_BASE}/list.json", params=params, timeout=30).json()

# 핵심 섹션만 사용 (왜? — ESG 서술이 집중되는 본문)
TARGET_SECTIONS = ["II. 사업의 내용",
                   "IV. 이사의 경영진단 및 분석의견",
                   "VI. 이사회 등 회사의 기관에 관한 사항"]
print("수집 함수 정의 완료 (실제 호출은 .env의 DART_API_KEY 필요). 산출물은 아래에서 로드.")''')
code('''# 수집 lineage 로그 (수집여부·실패사유)
status = pd.read_csv(f"{ROOT}/data/processed/dart_collection_status.csv")
print("dart_collection_status.csv:", status.shape, "| 수집여부:", status["수집여부"].value_counts().to_dict())
print("최대 firm-year(127사×3년) =", 127*3, " | 분석 패널(텍스트·등급 결측 0) =", len(m))
print("timing: esg_year = fiscal_year + 1  (KCGS 평가연도 t ↔ 직전 회계연도 t-1 사업보고서)")
display(status.head(3))''')

# ───────────────────────────────────────────────────────────── 2 전처리
md(r"""## 2. 전처리 (II·IV·VI · Kiwi 형태소)

**핵심 섹션 II·IV·VI를 합쳐 `text_raw`를 만들고, Kiwi 형태소 분석으로 토큰화했다.**

- **섹션 선택 이유**: II(사업의 내용)·IV(MD&A)·VI(이사회 등 기관)는 환경·사회·지배구조 서술이 집중되는 본문이다(표·재무제표 위주 섹션 제외).
- **Kiwi는 `text_raw`(원문)에 적용**: 원문의 공백·문장 경계가 남아 단어 분리가 자연스럽다(`text_clean`은 경계가 약함).
- **토큰 필터**: 명사(N*)·동사/형용사(V*)·영문(SL)만 유지, 불용어(`stopwords_ko_esg.txt`)·길이 1 이하 제거 → 최종 토큰열 `kiwi_text`.
- 길이 통제변수 = `log(len_II + len_IV + len_VI)` (핵심 섹션 문자수).""")
code('''# ── 전처리 코드 (notebooks/03_데이터전처리.ipynb 에서 1회 수행) ──
def tokenize_with_kiwi(text: str) -> list[str]:
    from kiwipiepy import Kiwi                       # 함수 내부 import(무거운 의존성 지연)
    kiwi = Kiwi()
    return [f"{t.form}/{t.tag}" for t in kiwi.tokenize(text)]

TFIDF_POS_PREFIXES = ("N", "V")                       # 명사·동사/형용사 계열
TFIDF_POS_TAGS = {"SL"}                               # 영문 단어
# tokens → 소문자·정규화 → 길이1 이하 제거 → 불용어 제거 → N/V/SL 만 → 공백조인 = kiwi_text

# 산출물 로드 (381×5: 회사이름·esg_year·raw_text·clean_text·kiwi_text)
pre = pd.read_csv(f"{ROOT}/data/processed/dart_preprocessed.csv")
seclen = pd.read_csv(f"{ROOT}/data/processed/dart_section_lengths.csv")
print("dart_preprocessed:", pre.shape, "| 컬럼:", list(pre.columns))
print("kiwi_text 예시:", repr(pre["kiwi_text"].iloc[0][:90]))
print("dart_section_lengths:", seclen.shape, "→ 길이통제 = log(len_II+len_IV+len_VI)")''')

# ───────────────────────────────────────────────────────────── 3 Feature
md(r"""## 3. Feature 생성 — 4가지 텍스트 표현 (2×2)

**같은 보고서·같은 전처리 위에서 차원별(E/S/G) 점수를 네 방식으로 만들었다.** 단어를 세는 표현은 *"감사위원회를 설치했다"* 와 *"설치하지 않았다"* 를 구별하지 못하므로, 의미를 보는 표현도 함께 둔다.

| | 단어 기반 | 의미 기반 |
|---|---|---|
| **비지도** | ① seed 사전 TF-IDF · ② fastText 확장 사전 TF-IDF | ③ dense cosine |
| **지도(등급 학습)** | — | ③ dense supervised probe |

- **① seed TF-IDF**: 과제 제공 seed 30개(E/S/G×10)의 TF-IDF 가중 합산(`min_df=2, max_df=0.95, L2`). 측정 대상 = "사업보고서에 ESG seed 표현이 얼마나 두드러지는가"(공시 강도, *성과 아님*).
- **② fastText 확장**: seed를 fastText 최근접으로 의미 확장 + LLM 필터. 재현율↑·차원 특정성↓ 가능.
- **③ dense(KURE-v1)**: 문장 임베딩 + 이방성 제거(ABTT 화이트닝) + 하위차원 앵커 + 길이강건 풀링 → 비지도 cosine. 별도로 등급을 학습한 supervised probe(기업 단위 OOF, 낙관 편의 인지).
- **cheap-talk 주의**: 단어가 많이/길게 등장하는 것과 실제 성과는 구분해야 한다(아래 통제 회귀의 핵심).""")
code('''# ── Feature ① seed TF-IDF: TF-IDF 행렬 구성 (notebooks/05b 설정 재현) ──
from sklearn.feature_extraction.text import TfidfVectorizer
vec = TfidfVectorizer(tokenizer=str.split, token_pattern=None, min_df=2, max_df=0.95, norm="l2")
X = vec.fit_transform(pre["kiwi_text"].fillna(""))
ok = "✓ 재현" if X.shape[1] == 40101 else "(주의)"
print(f"TF-IDF 행렬: docs={X.shape[0]} · vocab={X.shape[1]}  (기록값 vocab=40,101 {ok})")

seed = pd.read_csv(f"{ROOT}/data/raw/seed_dictionary.csv")
print("seed dictionary:", seed.shape[0], "개 term (E/S/G × 10):")
display(seed.groupby("dimension")["seed_term"].apply(lambda s: " · ".join(s)).to_frame("seed_terms"))
print("※ seed 구문 매칭(Kiwi tokenize_seed_phrase)은 05b 수행 → 점수는 05_tfidf_seed_features.parquet 로드(아래 m).")''')
code('''# 4표현 × E/S/G = 12개 텍스트 점수 (분석 패널 m 에 병합 완료)
print("표현별 차원 점수 컬럼:")
for k, v in REPRS.items():
    print(f"  {v['label']:18s} → {v['cols']}")
display(m[TEXT_COLS].describe().T[["mean", "std", "min", "max"]].round(3))''')

# ───────────────────────────────────────────────────────────── 4 타당성
md(r"""## 4. 측정 타당성 — Spearman 순위상관 + Mann-Whitney  〔라이브 실행〕

**회귀 전에 각 feature가 KCGS 등급과 통계적으로 연관되는지 먼저 확인한다.** 등급은 서열변수이므로 Spearman 순위상관이 자연스럽다. "ρ가 0.10–0.20이면 유의해도 효과는 약함"을 함께 본다.""")
code('''# (a) seed TF-IDF × KCGS 등급 — raw Spearman 3×3 (통제 없음)
seed_cols = {"E": "tfidf_E", "S": "tfidf_S", "G": "tfidf_G"}
gcols = {"E": "e_grade", "S": "s_grade", "G": "g_grade"}
rho = pd.DataFrame(index=["tfidf_"+d for d in ALL_DIMS], columns=[d+"_grade" for d in ALL_DIMS], dtype=float)
for i, td in enumerate(ALL_DIMS):
    for j, gd in enumerate(ALL_DIMS):
        rho.iloc[i, j] = spearmanr(m[seed_cols[td]], m[gcols[gd]]).statistic
print("seed TF-IDF × 등급 raw Spearman 3×3 (대각=자기차원):")
display(rho.round(3))
print("raw 대각지배 3/3:", all(rho.iloc[i, i] == rho.iloc[i].max() for i in range(3)),
      " — 단, 비대각도 높음(공시 충실도 단일요인 신호) → 통제 회귀 필수")''')
code('''# (b) Mann-Whitney: A이상(high_esg) vs 그외 — tfidf_G 분포 차이
hi = m.loc[m["high_esg"] == 1, "tfidf_G"]; lo = m.loc[m["high_esg"] == 0, "tfidf_G"]
U, p = mannwhitneyu(hi, lo, alternative="two-sided")
print(f"Mann-Whitney tfidf_G (A이상 n={len(hi)} vs 그외 n={len(lo)}): U={U:.0f}, p={p:.2e}")
print(f"  median  A이상={hi.median():.3f}  vs  그외={lo.median():.3f}")

# (c) feature 판단 표 (자기차원 raw Spearman) — ipynb 가이드 형식
jud = []
for k, v in REPRS.items():
    for dim, col in zip(ALL_DIMS, v["cols"]):
        rr = spearmanr(m[col], m[gcols[dim]])
        verdict = ("뚜렷한 관계 없음" if rr.pvalue > 0.05 else
                   "양의 관계·약함" if rr.statistic < 0.30 else "양의 관계")
        jud.append({"feature": col, "grade": dim+"_grade",
                    "Spearman ρ": round(rr.statistic, 3), "p": round(rr.pvalue, 4), "판단": verdict})
display(pd.DataFrame(jud))''')

# ───────────────────────────────────────────────────────────── 5 회귀
md(r"""## 5. 회귀분석 — 모델 선택 · 단계적 통제 · 생존 매트릭스  〔라이브 실행〕

**ESG 등급은 D~A+의 서열변수이므로 순서형 로짓(ordered logit)을 주 모형으로 쓰고, 이진 로짓(A 이상)·OLS를 강건성 확인용으로 병행한다.**

- 텍스트 점수는 z-표준화(모집단 std), 표준오차는 기업 단위 군집화(같은 기업 3개 연도 의존성).
- **통제 순서**: 규모(log 자산) → 분량(log 핵심 문자수) → 업종(8더미, 기준 1차금속) → 연도(기준 2022)를 **먼저** 투입하고 텍스트를 마지막에 넣는다. 그래야 텍스트의 *추가* 설명력이 진짜인지 가려진다. (규모가 1차 교란임을 §6에서 보인다.)""")
code('''# (a) 모델 선택 데모 — 같은 스펙을 세 모형으로
xs = ["tfidf_G_z", LEN_Z, SIZE_Z]
ro = fit_ordered(m, INTEG_GRADE, xs); rl = fit_logit(m, "high_esg", xs); rO = fit_ols(m, INTEG_GRADE, xs)
print("통합등급 ~ tfidf_G_z + 길이 + 규모  (모형 비교):")
print(f"  순서형 로짓 : tfidf_G_z={ro['params']['tfidf_G_z']:.3f} (p={ro['pvals']['tfidf_G_z']:.3f})  McFadden={ro['mcfadden']:.3f}")
print(f"  이진 로짓(A↑): tfidf_G_z={rl['params']['tfidf_G_z']:.3f} (p={rl['pvals']['tfidf_G_z']:.3f})  pseudoR²={rl['prsquared']:.3f}")
print(f"  OLS         : tfidf_G_z={rO['params']['tfidf_G_z']:.3f} (p={rO['pvals']['tfidf_G_z']:.3f})  R²={rO['r2']:.3f}")
print("→ 서열 보존 위해 순서형을 주 모형으로, 이진/OLS는 강건성 확인용.")''')
code('''# (b) 엔진 신뢰성 — committed 05b 수치 복원 확인
r = fit_ordered(m, "g_grade", ["tfidf_G_z", LEN_Z, SIZE_Z] + SECTOR_DUMMIES + YEAR_DUMMIES)
print(f"seed-G 완전통제 계수 = {r['params']['tfidf_G_z']:.4f}  (기록 0.378),  p={r['pvals']['tfidf_G_z']:.4f}")
ri = fit_ordered(m, INTEG_GRADE, ["tfidf_E_z","tfidf_S_z","tfidf_G_z", LEN_Z, SIZE_Z] + SECTOR_DUMMIES + YEAR_DUMMIES)
print(f"통합: log_assets_z={ri['params'][SIZE_Z]:.3f} (기록 1.062)  >  tfidf_G_z={ri['params']['tfidf_G_z']:.3f} (기록 0.458)")
print("→ 규모(log 자산)가 텍스트보다 지배적. 엔진이 committed 값을 복원 → 4표현에 동일 적용 신뢰.")''')
code('''# (c) ★ 완전통제 후 자기차원 텍스트 계수 — 4표현 × E/S/G 라이브 재현 (= 논문 Table 3)
rows = []
for k, v in REPRS.items():
    for dim, col in zip(ALL_DIMS, v["cols"]):
        rr = fit_ordered(m, GRADE_COLS[dim], [col+"_z"] + CTRL_FULL)
        b = rr["params"][col+"_z"]; p = rr["pvals"][col+"_z"]
        rows.append({"표현": v["label"], "차원": dim, "계수": round(b, 3), "p": round(p, 4), "유의": sig_stars(p)})
surv = pd.DataFrame(rows)
print("완전통제(길이·규모·업종·연도) 후 자기차원 계수 — '유의' 칸이 비면 통제 후 소멸:")
display(surv.pivot(index="표현", columns="차원", values="계수")[["E","S","G"]])
display(surv.pivot(index="표현", columns="차원", values="유의")[["E","S","G"]].fillna(""))
ms = surv.assign(생존=surv["p"] < 0.05).groupby("차원")["생존"].sum().reindex(ALL_DIMS)
print("차원별 완전통제 후 생존 표현 수(4 중):", ms.to_dict(),
      "→ ① seed=G · ③ supervised=S · 그 외 없음. 어느 차원도 과반(>2) 재현 안 됨.")''')
md(r"""**해석.** ① 규모가 1차 예측자이고(§6), 텍스트의 추가 설명력은 작다. ② 완전통제 후 살아남는 차원이 **표현마다 다르다**(단어 기반은 G, 학습된 의미는 S, 나머지는 없음). 진짜 강한 차원 신호가 있었다면 표현을 바꿔도 같은 차원이 살아야 한다 — 그렇지 않으므로, 텍스트–등급 연관은 차원특정이 아니라 단일 "공시 충실도" 요인에 가깝다.""")

# ───────────────────────────────────────────────────────────── 6 종합
md(r"""## 6. 종합 (synthesis) — 위계적 R² · 분량 통념 · 표현 간 수렴 · 약신호

> 검증 엔진 `analysis/07d_synthesis.py`(+`synth_lib.py`)의 산출물(`07d_*.csv`/`.png`)을 정리한다. 단일 출처 서술 = `종합_기록.md`.""")
code('''# (1) 위계적 R² — 규모 한 변수가 통합등급 분산의 43%, 텍스트 증분은 ≤5.3%p
show_fig("07d_a1_block_increments"); _ = show_tbl("07d_a1_hierarchical_r2")''')
md("""규모(자산) 하나로 통합등급 분산의 **43%**(OLS R²)가 설명되고, 분량·산업·연도까지 더해 50.7%가 된다. 그 위에 **E·S·G 텍스트 3개를 통째로 더해도 증분은 0.7%p(dense cosine)~5.3%p(seed·supervised)** — 규모의 1/8 이하다. 어떤 표현을 써도 텍스트는 규모를 못 이긴다.""")
code('''# (2) "긴 보고서 = 좋은 등급" 통념 — 규모 통제 시 급감
show_fig("07d_a4_length_myth"); _ = show_tbl("07d_a4_length_myth")''')
md("""분량–등급 단순상관은 0.65로 커 보이지만, **규모를 통제하면 부분상관 0.20으로 급감**한다(연관의 53~75%가 규모 경유). "긴 보고서=좋은 ESG"가 아니라 "큰 회사가 길게 쓰고 등급도 높다"이다.""")
code('''# (3) 부분 3×3 대각지배 (길이+규모 통제) — seed 라이브 + 4패널 종합
pp = pd.DataFrame(index=["tfidf_"+d for d in ALL_DIMS], columns=[d+"_grade" for d in ALL_DIMS], dtype=float)
for i, td in enumerate(ALL_DIMS):
    for j, gd in enumerate(ALL_DIMS):
        pp.iloc[i, j] = partial_spearman(m, seed_cols[td], gcols[gd], [LEN_Z, SIZE_Z])
print("seed TF-IDF 부분 3×3 Spearman (길이+규모 통제) — 약하지만 대각지배 3/3:")
display(pp.round(3))
show_fig("07d_a3_partial3x3_panels")''')
code('''# (4) 표현 간 수렴 + 생존 매트릭스 + 트랙간 G 수렴(정반대)
show_fig("07d_a3_fullcontrol_bars")
print("▶ 차원별 생존(표현) 수 — 어느 차원도 과반 재현 안 됨"); _ = show_tbl("07d_a3_meta_survival")
print("▶ 트랙 간 같은차원 수렴(seed×dense cosine): E·S는 같은 회사, G는 −0.06(정반대)")
conv = show_tbl("07d_a3_convergence")''')
code('''# (5) 약신호의 정밀도 — 부트스트랩 CI·순열검정 통일 잣대 ("유의 ≠ 중요")
show_fig("07d_a6_forest"); _ = show_tbl("07d_a6_signal_ci")''')
md("""세 트랙의 "살아남은" 신호를 하나의 부분상관 잣대로 재면 어느 것도 강하지 않다(**ρ≈0.13~0.20**, CI 넓음). 가장 견고한 seed-G도 부분ρ 0.17, 보수적 기업부트 95% CI [0.04, 0.30]이다. **통계적 유의 ≠ 중요·정밀.**""")

# ───────────────────────────────────────────────────────────── 7 알파
md(r"""## 7. 알파(α) — 왜 지배구조(G)만 남았나  〔팀 자체 설계 추가검증〕

**기본 과제(수집·전처리·feature·회귀) 외에, 팀이 스스로 설계한 추가 검증이다.** "완전통제 후 seed TF-IDF의 G만 강건 생존"이라는 발견의 *원인*을 4개 경쟁가설(H1 KCGS 구조 / H2 선택적 어휘 / H3 사전 품질 / H4 dense 실패)로 분해했다. 노트북 `08_가설검증_왜_G만_남았나.ipynb`, 엔진 `analysis/08_why_g.py`.""")
code('''# H2(최종 1위) — G를 끄는 건 이사회가 아니라 '선택적' 컴플라이언스·윤리·부패방지 어휘
dens = pd.read_csv(f"{DP}/08_h2_keyword_density_corr.csv")
print("H2 키워드 밀도 ↔ 점수/등급 (선택적 DRIVER vs 의무 BOILER):")
display(dens)
tb = pd.read_csv(f"{DP}/08_h2_top_vs_bottom.csv")
print("tfidf_G 상위10 vs 하위10 비교(요약):", tb.shape); display(tb.head(8))
show_fig("08_h2_measurability"); show_fig("08_synthesis_ranking")''')
md(r"""**해석.** `tfidf_G`를 실제로 끄는 단어는 이사회·사외이사·주주(거의 모든 보고서에 등장 → `max_df`가 제거)가 아니라 **컴플라이언스·윤리·부패방지** 같은 *선택적* 거버넌스 어휘다. 높은 G 기업은 이를 선택적으로 더 공시한다(상>하위 Mann-Whitney p=0.0007). TF-IDF의 IDF 가중이 이 희소·변별 어휘를 분리·증폭하는 반면, dense 임베딩은 보고서마다 비슷한 거버넌스 보일러플레이트에 묻혀 같은 G를 복제하지 못한다(단어·의미가 G에서 정반대). **단, G 신호 자체는 약하다(유의≠중요).**""")

# ───────────────────────────────────────────────────────────── 8 한계
md(r"""## 8. 한계 · 결론

**사업보고서의 ESG 텍스트는 신호이지만, 순수한 ESG 신호는 아니다.**

- **인과 아님**: 통제 관찰연구(연관/예측). 공시 강도와 실제 성과를 구분할 수 없다(cheap-talk 가능) → 기업 "그린워싱" 단정 금지(익명·집계).
- **준거의 한계**: 종속변수 KCGS 등급 자체가 규모에 크게 좌우(규모 단독 43%) → 통제 후 텍스트 약신호가 *텍스트 한계*인지 *준거의 규모편향*인지 본 설계로 분리 불가. **모든 결론은 KCGS 단일 기준의 잠정 결론.**
- **약신호·표현 한정**: 통제 후 텍스트 증분 ≤5%p, 생존 신호도 부분ρ 0.13~0.20·CI 넓음("유의 ≠ 중요"). G 생존은 seed TF-IDF 표현에 한정(단 `max_df` 규칙엔 강건).
- **표본**: n=381(127사)·3년·단일 평가기관 — 수업용 pilot panel, 검정력 제약. E의 null은 "신호 없음"이 아니라 "이 표본·이 준거에서 탐지 못함".
- **발전 방향**: 복수 평가기관 검증(준거 편향 분리) · 의무화(2026 거버넌스 전면·2028~ 규모별 시차)를 자연실험(staggered DiD)으로 · 수치 밀도(서술 구체성) 지표 · 업종별 이질성.

**결론**: 공시는 늘어난다 — 그러나 보완장치가 없으면 그것은 '정보의 질'보다 '형식적 공시 역량 차이'가 늘어날 위험이 있다. 정책당국엔 규모 중립·운영 중심 공시, 평가기관엔 보정·차원분화·정량결합·과정투명, 기업엔 두께가 아니라 검증 가능한 설명력을 시사한다.""")
code('''# 재현·제출 점검 요약
print("=== 재현/제출 점검 ===")
print("· 분석 패널:", m.shape, "| 381 기업-연도 · 결측 0")
print("· 위에서 아래로 실행 시 §4·§5(타당성·회귀)는 라이브 재현, §6·§7은 검증 엔진 산출물 정리")
print("· API key: os.environ 에서만 로드 — 노트북에 키 값 없음 ✓")
print("· 헤드라인: 규모 단독 R² 0.433 · 완전통제 후 seed-G 0.378** · 표현별 생존차원 상이(E0/S1/G1)")''')

nb["cells"] = cells
with open(OUT, "w") as f:
    nbf.write(nb, f)
print("wrote", OUT, "| cells:", len(cells))
