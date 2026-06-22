# ESG-DART · 사업보고서의 ESG 언어는 무엇을 측정하는가

> **한 줄 질문** — 사업보고서에 적힌 ESG 텍스트를 점수화하면, 그 점수는 *실제 ESG 수준*을 재는가,
> 아니면 *기업 규모·공시 역량*을 재는가?

한국 OpenDART 사업보고서 **127사 × 3년 = 381 기업-연도**의 ESG 서술을 **3가지 텍스트 표현**으로
점수화하고, 그 점수가 **KCGS ESG 등급**과 어떻게 연관되는지 순서형 회귀로 검증한 텍스트 측정타당성 연구입니다.

비정형데이터분석 텀프로젝트 · 2조.

---

## 핵심 결과 (TL;DR)

- 등급 ↔ 공시 **분량**의 상관이 ρ ≈ **.58–.63**으로 높고, 등급 ↔ **규모(log 자산)**가 이를 지배한다.
- 길이·규모·업종·연도를 **완전통제**하면 텍스트의 추가 설명력은 **약(weak)~null**로 줄고, **규모가 1차 예측자**
  (통합등급 R²의 **약 43%**)가 된다.
- 통제 후 **살아남는 차원이 "측정 방법"마다 다르다**:

  | 표현 (track) | 통제 후 생존 신호 |
  |---|---|
  | ① seed TF-IDF | **G(지배구조) 0.38\*\*** (사전 기반에서만 강건) |
  | ② fastText 확장 사전 | 없음 |
  | ③ dense (KURE-v1) cosine | 없음 (E 시사하나 비강건) |
  | ③ dense supervised probe | **S(사회) 0.55\*** |

- **함의** — 사업보고서 ESG 텍스트 점수는 상당 부분 *규모·공시 역량*을 재며(cheap-talk 가능성),
  결론은 텍스트를 *어떻게 측정했는지*에 의존한다. 지배구조(G)를 텍스트로 잡으려면 사전 기반이 맞고
  범용 임베딩은 부적합하다.

> ⚠️ 연관/예측이며 **인과 아님**. "유의 ≠ 중요"(효과크기·CI 병기). KCGS 단일 기준의 잠정 결론.

---

## 연구 질문

- **RQ1** — ESG 텍스트 점수는 KCGS 등급과 연관되는가? (통제 전)
- **RQ2** — 기업 규모·공시 분량을 통제한 뒤에도 텍스트의 추가 설명력이 남는가?
- **RQ3** — 결론이 텍스트를 *어떻게 측정했는지*(표현 방식)에 의존하는가?

---

## 방법 개요

**데이터** — OpenDART 사업보고서(127사×3년). 본문 섹션 **II·IV·VI**를 core로 사용(+VIII·XI 확장),
`kiwipiepy` 형태소 분석. 라벨 = KCGS ESG 등급(통합·E·S·G), 매칭 `esg_year = fiscal_year + 1`.

**3가지 텍스트 표현**
1. **seed TF-IDF** — E/S/G 각 10개씩 **seed 사전 30개** 기반 점수.
2. **fastText 확장 사전** — seed 최근접 후보를 fastText로 추출 → LLM 필터로 정제한 확장 사전.
3. **dense (KURE-v1)** — 한국어 문장 임베딩. 앵커 cosine + supervised probe 두 방식.

**통일 회귀 스펙 (3트랙 공통 = 비교 공정성)**
- 순서형 `OrderedModel(logit)` · **기업 cluster SE**(`groups=stock_code`) · z 표준화
- 단계적 통제: `text_only → 길이 → 규모 → 업종 → 연도`
  (길이 `log_core_doc_len`, 규모 `log_assets`, 업종 sector 8더미, 연도 기준 2022)
- 강건성: 이진 로짓 + OLS, 통합 점수는 PC1 동반
- 분석 단위/키: `doc_id = {stock_code(6자리)}_{fiscal_year}` (회사명 단독 merge 금지)

상세 설계·수치·caveat는 [`docs/records/`](docs/records/)의 트랙별 기록 문서가 **단일 출처**입니다.

---

## 폴더 구조

```text
esg-dart-project/
├── ESG_최종보고서.docx              # 📄 제출물① — 논문형 최종 보고서
├── notebooks/
│   ├── 최종제출_분석노트북.ipynb     # 📓 제출물② — 통합 분석 노트북(47셀, 실행 출력 포함)
│   ├── 01_데이터수집 … 11_논문방어   # 단계별 파이프라인(수집→전처리→3트랙→종합→심화)
│   └── archive/                     # 은퇴/잡 노트북
├── analysis/                        # 분석 엔진·빌더 (repro_lib · synth_lib · 07d_synthesis · _build_*)
├── scripts/                         # LLM 후보필터 등 보조 스크립트
├── plan/                            # 설계 문서(02_anchors.md = dense 앵커 입력)
├── reports/
│   ├── figures/                     # 분석 그림
│   └── presentation_figures/        # 발표용 그림(png·pdf)
├── docs/
│   ├── records/                     # 트랙별 기록(단일 출처): TF-IDF·dense·fastText·종합·왜_G만
│   ├── drafts/                      # 논문/설계 초안
│   ├── advice/                      # 지도 피드백
│   ├── presentation/               # 발표자료(marp·pdf·pptx)
│   └── assignment_guides/           # 과제·DART·KCGS 가이드
├── data/                            # 🔒 비공개(gitignore) — 아래 '데이터 확보' 참고
│   ├── raw/                         #    원천 4파일
│   └── processed/                   #    중간 산출물(대용량)
├── outputs/                         # 결과 안내·종합 HTML
├── pyproject.toml · uv.lock         # uv 환경
└── CLAUDE.md                        # 저장소 색인(작업 가이드)
```

---

## 재현 방법

### 1. 환경 설정
```bash
# uv 설치 후
uv sync                       # 의존성 설치 (Python ≥ 3.12)
cp .env.example .env          # 또는 직접 생성 — 아래 키 입력
.venv/bin/jupyter notebook
```
`.env` 에 시크릿을 넣습니다(저장소에 포함되지 않음):
```
DART_API_KEY=...              # OpenDART 무료 발급 (수집 단계에만 필요)
ANTHROPIC_API_KEY=...         # fastText 후보 LLM 필터에만 필요
```

### 2. 데이터 확보 🔒
**핵심 원천 파일은 저장소에 포함**되어 있습니다 — `data/raw/`:
`company_master.csv`(회사목록 + KCGS 등급 + 업종) · `seed_dictionary.csv`(E/S/G seed 30개) · `stopwords_ko_esg.txt`(불용어).

**저장소에 없는 것**(용량·수집 필요):

| 파일/자료 | 내용 | 확보 방법 |
|---|---|---|
| `CORPCODE.xml` (29MB) | stock_code(6) → corp_code(8) 매핑 | OpenDART에서 다운로드 |
| 사업보고서 본문 | 분석 대상 텍스트 381건 | `DART_API_KEY`로 수집(`01·01b` 노트북) |
| `data/processed/*` | 중간 산출물(대용량) | 노트북 파이프라인으로 재생성 |

> 본문 텍스트는 포함 원천에 없으므로, *처음부터* 재현하려면 `DART_API_KEY`로 사업보고서 381건을 수집해야 합니다.
> 다만 노트북에 **실행 출력이 커밋**되어 있어, 재실행 없이도 결과는 확인할 수 있습니다.

### 3. 실행 순서
```
01·01b 수집 → 02 EDA → 03 전처리 → 04 피처
   → 05b seed TF-IDF · 05c fastText 확장 · 06/07/07b dense
   → 07d 종합 → 08~11 심화/방어
   → notebooks/최종제출_분석노트북.ipynb   (통합 재현)
```
무거운 단계(DART 수집·Kiwi 전처리·dense GPU 인코딩·fastText 학습)는 **게이트 방식**으로
1회 산출물을 캐시 로드합니다(키/GPU 없으면 캐시 폴백, `RUN_FROM_RAW=force`로 강제 재계산).
가벼운 분석(전처리·seed TF-IDF·타당성·회귀)은 로컬 CPU에서 committed 값을 1e-6 내로 복원합니다.

> **경로 주의** — 노트북은 절대경로 `ROOT="/Users/home1/esg-dart-project"`를 사용합니다.
> 다른 환경에서는 `analysis/repro_lib.py`가 환경변수 `ESG_ROOT`를 지원하며, 노트북 상단 `ROOT`도 맞춰 수정하세요.

---

## 산출물

| | 파일 |
|---|---|
| 📄 **최종 보고서** | [`ESG_최종보고서.docx`](ESG_최종보고서.docx) — 논문형 보고서(RQ1/2/3·Table 1~4·부록) |
| 📓 **분석 노트북** | [`notebooks/최종제출_분석노트북.ipynb`](notebooks/최종제출_분석노트북.ipynb) — 보고서 근거 코드(47셀, 실행 출력 포함) |

노트북은 **실행 출력이 커밋**되어 있어, 직접 재실행하지 않아도 전체 분석 흐름과 결과 수치를 그대로 볼 수 있습니다.

---

## 환경

uv(`uv.lock`) · Python ≥ 3.12. 핵심 라이브러리:
`pandas` · `scikit-learn` · `statsmodels` · `gensim` · `kiwipiepy`(형태소) ·
`sentence-transformers`/`torch`/`transformers`(dense) · `matplotlib`/`seaborn`. dev: `nbclient` · `nbconvert`.

---

## 한계

- **연관/예측이며 인과 아님.** 결론은 KCGS 단일 평가 기준의 잠정 결론이다.
- 공시 **강도 ≠ 실제 성과**(cheap-talk 가능성). "유의 ≠ 중요" — 효과크기·신뢰구간을 함께 본다.
- 표본 n = 381(127사×3년)로 제한적이며, 텍스트 표현·앵커·seed 선택에 따른 측정 인공물 가능성이 있다.
