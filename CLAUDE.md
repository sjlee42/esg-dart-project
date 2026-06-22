# CLAUDE.md

Claude Code 가이드. **이 파일은 색인이다 — 자세한 건 아래가 가리키는 문서를 읽어라.**

OpenDART 한국 사업보고서(127사×3년 = 381 기업‑연도)의 ESG 서술을 3가지 텍스트 표현
(seed TF‑IDF · fastText 확장 · dense KURE‑v1)으로 점수화해 KCGS ESG 등급과 회귀 비교하는 파이프라인.
**현 상태(2026‑06): 수집·전처리·3트랙·종합 분석 전부 완료. 레포 정리(2026‑06‑22): 문서를 `docs/`로 재배치,
정본 제출 노트북 `notebooks/최종제출_분석노트북.ipynb` 재생성(은퇴본·잡노트는 `notebooks/archive/`).**
분석 코드 수정 전 해당 기록 .md(`docs/records/`)를
먼저 읽어라 — 결과의 단일 출처는 코드 주석이 아니라 기록 문서다.

## 핵심 결과 (오인용 금지)
등급↔분량 ρ≈.58~.63, 그리고 등급↔규모(log 자산)가 지배. 길이·규모·업종·연도 완전통제 후
텍스트는 약~null이고 규모가 1차 예측자(통합등급 R²의 43%). 통제 후 생존 차원이 표현마다 다름:
**①seed=G 0.38\*\* · ②확장=없음 · ③dense cosine=없음(E 시사·비강건) · ③dense supervised=S 0.55\***.
통합 supervised S_sup 1.53은 공선성 왜곡(VIF 9.68)이라 인용 금지 → 매칭 S 0.55\* 또는 PC1 인용.

## 궁금하면 여길 봐라 (단일 출처)
| 알고 싶은 것 | 파일 → 내용 |
|---|---|
| **제출물 ①② (정본)** | 보고서 `ESG_최종보고서.docx`(루트) + 분석 노트북 `notebooks/최종제출_분석노트북.ipynb`(47셀·논문 정합) — 빌더 `analysis/_build_final_submission.py` |
| 전체 분석 설계·통제 원칙 | 본 파일 '깨면 안 되는 불변식' 섹션 + `docs/records/`(트랙별 상세) |
| **3트랙 종합 결과** | `docs/records/종합_기록.md`(단일 출처) → 종합 임팩트 분석 7종. 엔진 `analysis/07d_synthesis.py`(+`synth_lib.py`), 노트북 `notebooks/07d_synthesis_impact.ipynb`, 표 `data/processed/07d_*.csv`·그림 `reports/figures/07d_*.png` |
| 트랙별 상세·회귀·caveat | `docs/records/TF-IDF_기록.md`·`docs/records/fastText_기록.md`·`docs/records/dense_기록.md` → ①②③ 논문/PPT 기초자료 |
| dense 트랙 진행·게이트 | `plan/AGENT.md`(thin 컨트롤러, 먼저 읽기) → "현재 단계"가 가리키는 `plan/0X_*.md` 1개만 추가로 |
| TF‑IDF+seed 점수화 상세 | `reports/03_preprocessing_step5_flow.md` |
| 교수/비전공자 총정리 | `outputs/ESG_텀프로젝트_과정정리.html`(자기완결 단일파일, 탭6·그림 base64) · 안내 `outputs/00_결과안내_INDEX.md` |
| 발표·초안·평가방법론 | `docs/presentation/발표자료_v2.md` · `docs/drafts/`(mini_paper·보고서 초안) · `docs/KCGS_ESG_평가방법론_정리.md`(KCGS 등급 방법론) |

## 파이프라인 (notebooks/, 순서 고정·산출물 이어받기)
01 수집 →(01b DART 업종·자산→`company_controls.csv`)→ 02 EDA → 03 전처리(`dart_preprocessed.csv`)
→ 04 피처(fastText) → `scripts/llm_filter_candidates.py`(LLM 후보필터). 트랙:
**05b** seed TF‑IDF · **05c** fastText 확장 · **06** dense baseline(실패케이스·**수정금지**)
· **07/07b** dense v2(무거운 인코딩·회귀는 Colab, 로컬은 셀 작성·검증) · **07d** 종합.
통합 재현·제출 = `notebooks/최종제출_분석노트북.ipynb`(빌더 `analysis/_build_final_submission.py`, 47셀·실행출력 포함). 은퇴/잡 노트북 = `notebooks/archive/`.

## 깨면 안 되는 불변식
- 단위 `stock_code×fiscal_year`. **키 `doc_id={stock_code zfill6}_{fiscal_year}`, 회사명 merge 금지.**
  등급 매칭 `esg_year=fiscal_year+1`. 결측은 0채움 말고 사유 기록.
- **통일 회귀 스펙(3트랙 공통=비교 공정성)**: 순서형 `OrderedModel(logit)` · 기업 cluster SE(groups=stock_code)
  · z(모집단 std ddof=0) · 단계적 통제 text_only→길이→규모→업종→연도. 길이=`log_core_doc_len`(log II+IV+VI 문자수),
  규모=`log_assets`, 업종=sector 8더미(기준 1차금속), 연도 기준 2022. 강건성=이진 로짓+OLS, 통합은 PC1 동반.
- 통제변수 `data/processed/`: `industry_sector_mapping.csv`(sector+log_assets, **stock_code zfill 안 됨→zfill(6) 후 merge**)
  · `dart_section_lengths.csv`. **공개 정책**: 핵심 원천 CSV만 추적(`data/raw/`의 `company_master.csv`·`seed_dictionary.csv`·`stopwords_ko_esg.txt`), `data/processed/` 전체·`CORPCODE.xml`·기타 `*.csv`는 gitignore(로컬 보존). 새 추적 CSV는 `.gitignore`에 `!` 규칙 필요.
- 전처리는 고정(실험 대상 아님). Kiwi는 `text_raw`에 적용. 섹션 II·IV·VI=core(+VIII·XI 확장).
  seed 30개 = `data/raw/seed_dictionary.csv`.

## 환경
uv(`uv.lock`)·Python 3.12+·Korean UTF‑8 경로 유지. `uv sync` / `.venv/bin/jupyter notebook`
/ `uv run python scripts/llm_filter_candidates.py`. 시크릿 `.env`(`DART_API_KEY`·`ANTHROPIC_API_KEY`, 템플릿 `.env.example`).
테스트·린트 없음 → 노트북 재실행으로 검증. **제출물② 재생성**: `uv run python analysis/_build_final_submission.py` → `.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/최종제출_분석노트북.ipynb`.
