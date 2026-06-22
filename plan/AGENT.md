# AGENT.md — Dense ESG v2 실행 컨트롤러 〔매 턴 먼저 읽기〕

> 이 파일은 **얇은 컨트롤러**다. 매 턴 **이 파일만 먼저** 읽고, "현재 단계"가 가리키는 상세 문서 **1개만** 추가로 연다. 모든 문서를 한꺼번에 읽지 말 것 — 컨텍스트 절약이 목적이다.

## 0. 목표 (한 줄)

상장기업이 사업보고서(`II·IV·VI`)에 쓴 **언어**와 KCGS가 매긴 **ESG 등급** 사이의 **연관 패턴**을 데이터로 확인한다. "공시가 등급을 결정했다"는 **인과 주장이 아니다.** 데이터: 127사 × 3개 사업연도(2022·2023·2024) = 381 기업-연도, 대응 KCGS `esg_year` 2023~2025. 모델: KURE-v1(bge-m3 한국어 파인튠, 1024d).

## 1. 에이전트 역할

너는 단순 설명자가 아니라 **데이터 분석 에이전트**다. 방법론을 설명하는 데서 멈추지 말고, 실제 분석 코드를 작성하고, 가능한 범위에서 실행해 결과를 검증하라. **코드만 생성하고 종료하지 않는다.**

## 2. 실행 환경 분리

- **로컬/현재 환경** — 데이터 구조 확인, 전처리 코드 작성·샘플 실행·품질 검증, 진단 코드 작성, Colab 실행용 코드 생성.
- **Google Colab(GPU T4)** — KURE-v1 임베딩 생성, 화이트닝, 풀링 실험, 지도 프로브 학습, 회귀 분석, 최종 결과·보고서 생성.
- 무거운 임베딩/회귀는 Colab. 로컬에서는 **전처리 검증 + Colab용 코드 생성까지**.

## 3. 작업 원칙 — 모든 셀은 "3종 세트"

숫자만 찍고 넘어가는 셀 금지. 전처리·피처·진단·회귀 막론하고 **모든 코드 셀**은 다음 셋을 포함한다.

1. **시각화** — 그림/표로 결과를 눈으로 확인(분포·히트맵·산점도·요약표).
2. **샘플 확인** — 실제 1~2건을 raw로 출력(어떤 문서가·어떤 문장이·어떤 점수가).
3. **해석 가이드** — 이 출력을 어떻게 읽나 / 무엇이 정상이고 무엇을 경계할지 마크다운·주석으로 명시.

목적: 비전공자도 셀 단위로 따라갈 수 있고, 특히 전처리 오류가 조용히 흘러가지 않게 한다.

## 4. 단계별 출력 규칙

각 단계는 반드시 ① 코드 작성 → ② 실행 가능 시 실행 → ③ 결과 확인 → ④ 결과 해석 → ⑤ **PASS / FAIL / REVIEW REQUIRED 선언** 순서를 따른다.

## 5. 반복 실행 루프 〔★ 사용자 협업 방식〕

이 프로젝트는 한 번에 끝까지 가지 않는다. **결과를 봐야 다음 코드를 쓰는 지점**에서 멈추고 사용자에게 넘긴다.

- **1차 실행** — 전처리를 검토하며 1차 코드를 작성 → 샘플 실행 → 결과 출력 → Gate 판정. 다음 코드가 그 결과에 의존하면 **거기서 멈추고 `REVIEW REQUIRED`** 로 선언, 사용자에게 결과를 제시한다.
- **2차 이후** — 사용자가 결과·피드백을 주면 그걸 반영해 **뒷코드를 재작성**하고 다음 게이트까지 진행한다.
- 이 사이클을 단계마다 반복한다. 한 턴에 여러 게이트를 건너뛰며 끝까지 코드를 쏟아내지 않는다.

## 6. 사용자 승인 규칙 〔하드 게이트〕

**전처리 Gate 1 PASS 이전에는** 임베딩 생성·지도 프로브·회귀를 **수행하지 않는다.** 전처리 검증이 완료된 후에만 전체 파이프라인을 확정한다.

## 7. Gate 요약 〔상세는 해당 문서〕

| Gate | 평가 | PASS 기준 | FAIL 시 |
|---|---|---|---|
| **G1 전처리** | 표/목차 제거·ESG문장 유지·비정상 장문/단문 없음 | 4항목 모두 충족 | → 전처리 복귀 (`04_preprocessing.md`) |
| **G2 분량누수** | `corr(feature, report_len)` | 기존 E .611/S .655/G .464 대비 **의미있는 ↓** | → 풀링/화이트닝 재설계 (`01`·`03`), **회귀 금지** |
| **G3 판별타당도** | 3×3 Spearman 대각지배 | 각 피처가 **자기 차원** 등급과 최고 상관 | → 앵커 재설계 (`02_anchors.md`), **회귀 금지** |
| **G4 다중공선성** | VIF | **< 10** | → PCA 합성요인 모델 (`05_regression.md`) |
| **G5 지도프로브** | 누설 방지 | GroupKFold + **OOF 예측만** 사용 | → 프로브 폐기 |

모든 Gate는 **PASS / FAIL / REVIEW REQUIRED** 중 하나를 반드시 선언한다.

## 8. 단계 목록 (§8) — 각 단계 = 1+ 셀, 3종 세트 필수

1. 환경·상수·데이터 로드
2. **전처리 재현·수정·샘플 검증 → Gate 1** 〔★ 여기서 멈춰 사용자 검토〕
3. 임베딩 (재)생성 — 캐시 무효화 로그
4. 화이트닝 적합·적용
5. 앵커 구성·품질 검증
6. 풀링 후보 생성 → 2축 선택 → **Gate 2**
7. 비지도 피처 `E_cos/S_cos/G_cos` 확정 → **Gate 3**
8. 지도 프로브 (GroupKFold) → **Gate 5**
9. 분석 테이블 병합 (피처+등급+통제)
10. 진단 (대각지배·누수·수렴·VIF) → **Gate 4**
11. 회귀 (차원별 × 통합 × {순서형·이진·OLS} × {cosine·supervised})
12. 최종 보고서 (HTML + Markdown)

## 9. 문서 맵 〔현재 단계에 필요한 것만 열기〕

- **`01_rationale.md`** — §0 질문 · §1 실패진단 · §2 처방 · §3 풀링 근거 → *피처 설계·풀링·진단 논리가 필요할 때*
- **`02_anchors.md`** — 앵커 하위차원 목록 + 앵커 품질검증 → *Step 5 앵커 만들 때* 〔선생님이 편집하는 파일〕
- **`03_features.md`** — 화이트닝·비지도 cosine·지도 프로브 → *Step 3~8 피처 생성*
- **`04_preprocessing.md`** — 전처리 반복루프·기존 파이프라인(복원)·수정 체크리스트·샘플 검증 → *Step 2 전처리*
- **`05_regression.md`** — 회귀 설계·VIF·타당도 진단 → *Step 10~11*
- **`06_outputs_limits.md`** — 산출물 목록·한계·가정 → *Step 12 보고서*

## 10. 빌드 산출물 위치

- 코드는 **새 노트북 `notebooks/07_dense_esg_v2.ipynb`** 에 작성한다. 기존 `notebooks/06_dence_cosine.ipynb`(베이스라인 = §1의 실패 케이스)는 **건드리지 말 것** — §7.1 개선 전/후 비교에 필요하다.
- 최종 Colab 노트북은 `outputs/` 에 생성: `features.csv`, `pooled_features.csv`, `diagnostics.csv`, `regression_results.csv`, `figures/*.png`, `final_report.md`, `final_report.html`. 마지막 셀에서 `outputs.zip`.

## 11. 열린 항목 / 블로커 〔진행 중 확인〕

- **[BLOCKER · Step 11]** 회귀 통제변수 `log_assets`(log 총자산)·`industry`(업종)가 아직 산출물에 없거나(자산) 결측이 큼(업종 기존 78% 결측). 회귀 전에 **사용자 제공 데이터** 확보가 필요하다. /Users/home1/esg-dart-project/data/processed/industry_sector_mapping.csv 에서 확인한다. 자산은 log(자산)을 이용하고, 산업은 대분류 산업기준을 이용한다.
- **[검증완료]** 계획서 §1·§3·§7 인용 수치는 실제 산출물과 일치(F2 대각지배·F4 풀링 평균|ρ| .391/.275/.100·수렴 대각 .503/.428/.288 확인).
- **[주의]** 화이트닝·앵커 하위차원·길이강건 풀링·지도 프로브·차원별 회귀·VIF·GroupKFold는 기존 노트북에 **없는 신규 작업**이다(06은 베이스라인만 구현). 새로 만든다.

---

## 현재 단계

**▶ 🟢 Dense ESG v2 파이프라인 Step 1~12 전부 Colab 실행 완료(07b 30셀). 모든 게이트 판정·산출물(`outputs/outputs.zip`) 생성됨. 새 컨텍스트 = 3트랙(dense/TF-IDF/fastText) 종합 논문 본문·PPT 작성, 또는 추가 robustness 요청 대응. 기록 3종(`dense_기록.md`·`TF-IDF_기록.md`·`fastText_기록.md`)이 작성 기초자료. 〔이하 과거 진행 기록〕 Step 11.2 (이진·OLS 강건성 + 통합 PCA). Step 9·10 Colab 실행 PASS — Step10 G4 PASS(통합cos maxVIF 4.89·통합sup 9.68(E_sup_z,경계)·차원 4.4), 누수 cosine E.29/S.26/G−.09(≪baseline) but supervised .58~.65(≈baseline, 길이학습→통제필수), 수렴 대각 E.45/S.30/G−.06(E·S만 TF-IDF와 수렴, G null). Step 11.1(순서형 회귀) **Colab 실행 완료 — 🔴결론정정: dense cosine 완전통제 후 생존 없음**(E 0.565***→규모서 0.269 p.068→0.255 p.117 비유의·S 길이서 즉사·G null; 통합도 전부 ns, log_assets 1.21** 지배). **supervised=S 생존**(probe가 cosine 놓친 S 포착) but 길이누수.6+통합 공선성왜곡(E_sup VIF9.68 부호뒤집힘)→PCA필요. 갱신 3트랙: seed=G/확장=없음/dense cos=없음(E시사 p.12)/dense sup=S. (07b 26셀, 8.2 미실행). Step 8.2 Colab 실행 대기.** **[Step8/G5 프로브 결과·중요·반전]** 분량 통제 후 probe OOF 부분ρ(예측 상한) **E .274 / S .275 / G .192** (probe leak ρ .58~.65=대부분 길이지만 통제 후에도 +). 비지도 cosine 부분ρ는 E .168/S .058/G .032 → **cosine·앵커가 S·G 신호를 놓침**(특히 S: .06 vs 상한 .27). 상한이 세 차원 비슷(~.19~.27)·차원특정 아님 → **modest한 단일 '공시품질' 신호가 verbosity 너머 실재**하나 cosine은 E만 포착. G5=PASS(GroupKFold 기업 OOF·누설 assert). 회귀(Step11)=**cosine·supervised 둘 다 × 통제{log(core 길이=II+IV+VI)+log(자산)+업종+연도}**(3트랙 통일안, 규모 항상 포함; report_len=문장수는 보조 robustness만).
**[G3]** FAIL(부분 대각지배 1/3=E만) but 피처 공선성 F2 대폭개선(E–S .844→.479·E–G→.123·S–G→.188). **[G2]** softmax0.05 채택·PASS. **[화이트닝]** ABTT(d=10). **[핵심 발견] 등급↔분량 ρ .58~.63(거대 교란)·부분ρ(분량 통제 순수신호) E~.15/S~.10/G~0, 풀링과 무관하게 평평 → own-grade 신호 대부분이 분량(F3/F5 데이터 확증). 정직한 결론: 텍스트↔등급 연관 E 약·S 미약·G null.** Step5 앵커: 최근접 문장 E/S/G 정확, 대각지배 E.46/S.36 성립·G.27<.30 실패(주시). Step4 ABTT 채택(raw 다른문서 .35→~0). nb07(14셀)=Step1+2+3.0, **07b(20셀,Colab)=Step3 인코딩+Step4 화이트닝+Step5 앵커+Step6 풀링/G2+Step7 G3+Step8 프로브/G5+Step8.2 부분3×3 정합(미실행)**. 채택 화이트닝 파라미터=`07_v2_whiten.npz`의 `abtt_top`. 다음 문서=`05_regression.md`(Step9~11).
- **Round1**(통째-Kiwi 재현): Gate1 기준3 FAIL — Kiwi가 표 섞인 거대입력에서 segmentation 붕괴(최장 222,465자=본문95%, 그 안에 `다.` 914개 → 마침표 부재가 아니라 거대입력이 원인. SOFT_NEWLINE 꺼도 악화 확인).
- **Round2**(확정, 사용자 승인): 문장분할만 교체 = **거친 청크(줄바꿈/종결경계) → 작은 조각만 Kiwi → MAX 초과 시 마침표/`입니다` 수동 폴백 → 최후 길이상한 절단**. 상수 `MAX_SENT_CHARS=1000, KIWI_CHUNK=2000, CLEAN_VERSION=v2-chunked-kiwi`.
- **결과**: 최장문장 222,465→1,000자, 본문30%+ 문서 55→0, 최장≥5000자 134→0, 총문장 111,107→**175,823(+58% 복구)**, 단문<15자 0.4%→3.4%(정상). 문장캐시 `data/processed/07_v2_sentences.parquet`(sig 무효화로 자동 재계산).
- **Step 3 산출**: 로컬 핸드오프 셀 = `EMB_SIG=402efddb86ca`(=md5(parquet_sig 462a9a3b4945 · KURE-v1 · 175,823))·manifest `data/processed/07_v2_emb_manifest.json`·플랜(추정 truncation 1.21%·배치 2,748). 실제 인코딩 = 신규 **Colab 노트북 `notebooks/07b_dense_esg_v2_colab.ipynb`**(전셀 3종세트): explode→KURE-v1(fp16/max_seq512/batch64/normalize)→`07_v2_sentence_emb.npz`(float16 1024d + doc_id/sent_idx + meta·sig). doc_id=`{stock_code}_{fiscal_year}`. 캐시무효화=npz meta.sig vs EMB_SIG.
- **Step 4 산출(07b 에 이어붙임)**: §5.1 평균제거+표준화 → **ABTT(d=10)·ZCA 둘 다** 적용·비교(같은/다른 문서 코사인 baseline 표·바차트 + 같은문서 쌍 cos 변화 + 파라미터 `data/processed/07_v2_whiten.npz` 저장). 비지도용 전체코퍼스 적합(순환성 없음). 합성검증: ABTT=이방성 제거+gap 보존 우세, ZCA=cov→I 완전등방(gap 더 축소 경향).
- **Step 5 산출(07b 5.1·5.2)**: `02_anchors.md` 기준문장 **27개**(E11·S9·G7, 하위차원 22개) → KURE-v1 인코딩 → ABTT 화이트닝(`whiten_abtt`, 문장과 동일) → 품질검증(3×3 대각지배 히트맵·하위차원 응집·앵커별 최근접 문장). 모델 미적재 세션이면 자동 로드. `S_w=whiten_abtt(E)`(화이트닝 문장)도 생성(Step6 재사용).
- **Step 6 산출(07b 6.1·6.2)**: 문장→차원=앵커 max → 풀링 후보 12종(docmean·topk{5,10,20}·max·topp{2,5,10}%·고분위 q90/q95·softmax{.05,.10}) × E/S/G → 신호(own-grade Spearman ρ)·누수(corr report_len) 표 + 차원별 프론티어 산점도. 채택=score(신호−누수) 최상위 → `07_v2_features_dense.csv`(E/S/G_cos+report_len+등급) 저장. **G2**: 채택 누수 vs 기존 E.611/S.655/G.464 비교 PASS/FAIL 자동판정. 등급은 company_master.csv 로드. 신호축 own-grade 사후선택→회귀 낙관 주의(P5).
- **Step 7 결과(07b 7.1, 실행됨)**: G3 FAIL(부분 대각지배 1/3=E만). 부분 3×3: E_cos(e.168/s.146/g-.04), S_cos(e.114/s.058/g.058), G_cos(e.10/s.185/g.03). 피처공선성 F2 대비 대폭↓(.844→.479 등). 단일요인+E만 유효 확정.
- **Step 8 결과(07b 8.1, 실행됨)**: probe OOF 부분ρ(상한) E.274/S.275/G.192, leak .60/.65/.58, cosine 부분ρ E.168/S.058/G.032. → cosine이 S·G 상한을 크게 하회(놓침). 산출 `07_v2_features_supervised.csv`(doc_id·E/S/G_sup). G5 PASS.
- **Step 9 결과(07b 21셀, 코드작성+로컬 머지검증·Colab 미실행)**: `feat`(cosine)+`sup_df`(supervised)+통제(`industry_sector_mapping.csv`의 sector·log_assets, `dart_section_lengths.csv`의 log_core_doc_len=log(II+IV+VI), `company_master.csv`의 통합 esg_grade_num) 를 doc_id `{stock_code}_{fiscal_year}` 1:1 병합 → **`07_v2_analysis_table.csv`**. 로컬 dry-run(실키 381·가짜피처): **381행·통제결측0·1:1 OK**, z-score(모집단std) E/S/G_cos·sup·log_assets·log_core_doc_len·report_len, 업종 더미 기준=1차금속(7개)·연도 기준=2022 → **05b TF-IDF 더미 스펙과 정확히 일치**(검증됨). high_esg=esg_grade_num≥4. **남은 건 Colab에서 실피처로 1회 실행해 감사숫자(381/0) 확인.**

### ▶▶ STEP 12 시작 가이드 (새 컨텍스트용) ◀◀ 〔Step 11.1 Colab 완료 · Step 11.2 코드 완료·로컬검증〕
- **읽을 문서**: 이 `AGENT.md` → 그다음 `plan/06_outputs_limits.md`(산출물·한계·가정)만 1개 추가로 연다.
- **코드 위치**: `notebooks/07b_dense_esg_v2_colab.ipynb`(Colab, 현재 **28셀**; Step 8.2·9·10·11.1·11.2 포함, 8.2·11.2 Colab 미실행)에 Step 12 이어붙임. **새 세션이면 위→아래 실행(8.1~11.2)**.
- **Step 11.1(Colab 완료) = 순서형 회귀**: dense cosine 완전통제 후 **생존 없음**(E 0.255 p.117·S/G null·통합도 ns, log_assets 1.21** 지배), **supervised=S 생존**(probe가 cosine 놓친 S 포착) but 통합 공선성 왜곡(E_sup VIF9.68). 저장 `07_v2_dense_*_ordered_logit_*.csv`(05b 스키마).
- **Step 11.2(코드 완료, Colab 미실행) = 강건성+PCA**: 이진 로짓(high_esg≥A·high_{dim})+OLS(완전통제 05)+통합 **PC1 합성요인**(공선성안전) 순서형 단계적. 저장 `07_v2_dense_robustness_binary_ols.csv`·`07_v2_dense_integrated_pca_ordered_logit.csv`. **로컬검증: binary/OLS/PCA 엔진 무오류 실행(robustness 36행·PCA 정상). dense PC1 생존여부는 Colab 확정**(cosine 개별 다 null→PC1도 죽을 가능성↑ = 통합 텍스트도 분량·규모).
- **Step 12(다음) = 보고서**: 3트랙 종합표 — **seed TF-IDF=G(.38\*\*) / fastText 확장=없음 / dense cosine=없음(E시사 p.12) / dense supervised=S**. 공통메시지=등급↔분량 ρ.58~.63·규모(log_assets) 1차 지배·통제 후 텍스트 약~null·표현별 생존차원 상이. 산출물 zip(`06_outputs_limits.md` 목록). 기록 갱신: `dense_기록.md`(정정된 회귀결과 반영 필요).
- **✅ 통제변수 확인 완료(BLOCKER 해소)**: `data/processed/industry_sector_mapping.csv` 에 **`sector`(대분류 8개)+`log_assets` 381행 전부**(결측 0), `data/processed/dart_section_lengths.csv` 에 `len_II/IV/VI`. **05b TF‑IDF 회귀가 이미 사용**. Dense Step9도 이 파일로 `stock_code×fiscal_year` 병합(주의: 이 파일 stock_code 는 zero‑pad 안 됨 → `zfill(6)`). 업종 기준범주=1차금속, 연도=2022.
- **그 뒤**: Step 10 진단(대각지배·누수·수렴·**G4 VIF<10**) → Step 11 회귀(차원별×통합 × {순서형·이진·OLS} × {cosine·supervised}, 통제=**{log(core 길이)+log(자산)+업종 sector+연도}** 3트랙 통일·기업 cluster SE·z‑score, 통합은 PCA 합성요인 병행 P5) → Step 12 보고서(`06_outputs_limits.md`). **TF‑IDF(05b/05c)와 동일 스펙으로 맞춰 종합표 작성.**
- **핵심 결과 요약(보고서 메시지)**: 등급↔분량 ρ.58~.63 지배 · 분량통제 후 텍스트신호 modest(~.2~.27, 단일 공시품질요인, 차원특정 약) · cosine은 E만 포착·supervised가 상한 · 화이트닝/앵커가 F2 공선성(.844→.48) 해결.
- **3트랙 종합(통일안 채택)**: 공통 통제={`log(II+IV+VI)` 길이, `log_assets` 규모}(규모 항상)·공통 판별잣대=부분 3×3|길이+규모·동일 ordered logit 스펙. 기록=`dense_기록.md`·`TF-IDF_기록.md`(seed ①)·`fastText_기록.md`(확장 ②). 완전통제 후 생존: **①seed=G(.38\*\*) · ②확장=없음(전부 n.s.) · ③dense=E(cosine)**. 규모가 1차 교란(역순 검증). 확장(fastText)은 신호 개선 못함(노이즈↑). **07b Step 8.2** = dense 부분3×3을 길이+규모로 정합(Colab 실행 시 가운데 패널이 종합 슬롯). TF-IDF는 로컬, dense는 Colab.
- **미해결**: 표잔재 제거(후보 d)·NUM_RUN_RE 보정(후보 e)은 결과 보고 결정. (통제변수 BLOCKER는 `industry_sector_mapping.csv`+`dart_section_lengths.csv`로 해소.)
- **참고(타 트랙 결과)**: seed TF‑IDF(05b) 통제 회귀 완료 → 완전통제 후 **G만 생존**(매칭 .38\*\*/통합 .46\*\*\*), E 경계·S null, **규모(log자산)가 지배 예측자**. Dense(E 우세)와 대조. 정리=`TF-IDF_기록.md`·`dense_기록.md`. VIF 전부<10.
**임베딩/회귀는 Gate1 PASS 후 단계별로(§6). 매 턴 이 줄을 현재 진행 단계로 갱신한다.**
