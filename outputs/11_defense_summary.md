# 논문 방어용 추가 분석 요약

## A-1. LMG/Shapley 상대기여도 분석
- 발견 여부: 새로 계산 완료. 규모 LMG OLS=0.236, share=46.6%; McFadden=0.099, share=49.0%.
- 관련 파일: `data/processed/11_defense_lmg_shapley.csv`, 기존 순차투입 `data/processed/07d_a1_hierarchical_r2.csv`.
- 핵심 수치: 기존 순차투입 규모 ΔR²=0.433; LMG 순위는 규모 0.236, 분량 0.201, 업종 0.069, 연도 0.001.
- 논문 반영 위치: 5-1 규모 설명력 순서 의존성 검증. 규모가 여전히 최대 기여.

## A-2. 다중검정 보정
- 발견 여부: Table 5 후보 12개 자기차원 완전통제 p-value 보정 완료.
- 관련 파일: `data/processed/11_defense_table5_p_adjusted.csv`, 원본 `data/processed/07d_a3_fullcontrol_coef.csv`.
- 핵심 수치: BH-FDR 생존 신호: ① seed TF-IDF-G β=0.378, q=0.041.
- 논문 반영 위치: 5-2 Table 5 다중검정 보정 주석/부록.

## A-3. 텍스트 점수 × 규모 상관표
- 발견 여부: 12×2 Spearman 계산 완료. log_assets와 절대상관 최대=0.698, log_length와 절대상관 최대=0.632.
- 관련 파일: `data/processed/11_defense_text_size_correlations.csv`.
- 핵심 수치: 상세 rho/p는 CSV 참조.
- 논문 반영 위치: 6-2 규모 편향 근거 표.

## A-4. 금융업 제외 강건성
- 발견 여부: 금융·보험 제외 후 재추정 완료. 표본 381→303.
- 관련 파일: `data/processed/11_defense_finance_excluded_hierarchical_r2.csv`, `data/processed/11_defense_finance_excluded_fullcontrol.csv`.
- 핵심 수치: 규모 ΔR² 0.433→0.502; seed-G β 0.378(p=0.0034)→0.406(p=0.00418); supervised-S β 0.550(p=0.013)→0.637(p=0.0167).
- 논문 반영 위치: 3-4 금융업 제외 강건성.

## A-5. 차원별 규모 설명력
- 발견 여부: E/S/G 각각 `등급 ~ log_assets` 계산 완료.
- 관련 파일: `data/processed/11_defense_dimension_size_r2.csv`.
- 핵심 수치: E: R²=0.444, p=7.4e-14, pseudo-R²=0.188; S: R²=0.400, p=6.8e-12, pseudo-R²=0.166; G: R²=0.362, p=1.3e-13, pseudo-R²=0.132.
- 논문 반영 위치: 4-6 G만 규모를 반영하는지 확인. 결과는 G만이 아니라 E/S/G 모두 규모 영향.

## B-1. 총자산 변수 확인
- 발견 여부: 확인 완료. `assets_fs_div` 분포={'CFS': 345, 'CFS_MANUAL': 18, 'OFS': 18}.
- 관련 파일: `data/processed/company_controls.csv`, `analysis/synth_lib.py`.
- 핵심 수치: 최종 `log_assets`는 `assets`의 로그. 기준은 CFS(연결) 우선이며 CFS 345건 + CFS_MANUAL 18건, OFS fallback 18건이 포함됨.
- 논문 반영 위치: 자료/변수 정의.

## B-2. '아홉 가지 점수' 확인
- 발견 여부: 확인 완료. 9개는 비지도 점수(seed TF-IDF 3 + fastText 확장 3 + dense cosine 3). 최종 종합표에는 dense supervised 3개를 더해 12개도 보유.
- 관련 파일: `analysis/synth_lib.py`, `analysis/_build_notebook.py`.
- 핵심 수치: 포함 9개=`tfidf_*`, `expanded_tfidf_*`, `E/S/G_cos`; 제외/별도=`E/S/G_sup`(등급을 학습한 상한/검증 점수).
- 논문 반영 위치: 측정치 구성 설명.

## B-3. KCGS 등급 연도 매칭 확인
- 발견 여부: 확인 완료.
- 관련 파일: `notebooks/보고용_분석노트북.ipynb`, `plan/04_preprocessing.md`, `analysis/synth_lib.py`.
- 핵심 수치: `doc_id={stock_code}_{fiscal_year}`, `esg_year=fiscal_year+1`; join key는 회사명 단독이 아니라 `company_name + esg_year` 및 최종 `doc_id`.
- 논문 반영 위치: 데이터 매칭/식별 전략.

## B-4. KCGS 평가체계 개정 여부
- 발견 여부: 내부 자료에서는 분석기간 중 평가체계 개정 사실을 직접 입증하는 파일을 발견하지 못함.
- 관련 파일: `협업가이드자료/KCGS_ESG_평가방법론_정리.md`, `조언.md`.
- 핵심 수치: 내부 근거만으로 '변경 없음'이라고 단정 불가. 논문에는 '내부 자료 기준 확인 불가/한계'로 표기 권장.
- 논문 반영 위치: 한계/자료 설명.

## B-5. 업종 분포
- 발견 여부: 계산 완료.
- 관련 파일: `data/processed/11_defense_industry_distribution.csv`.
- 핵심 수치: 상위 업종 금융·보험: 78건(20.5%), 26사; 유통·물류·건설·기타: 66건(17.3%), 22사; 화학·소재: 63건(16.5%), 21사.
- 논문 반영 위치: 표본 설명.

## C/D. 기타 확인
- C-1 max_df=1.0: 기존 문서에서 seed-G 0.38→0.51 강건성 언급 발견(`analysis/_build_notebook.py`, `outputs/발표자료_v2.md`).
- C-2 앵커/ABTT/whitening: dense 개선 기록 발견(`plan/01_rationale.md`, `notebooks/07b_dense_esg_v2_colab.ipynb`).
- C-3 OOF 검증: GroupKFold 기업 단위 OOF 및 누설 방지 기록 발견(`outputs/final_report_detailed.html`, `notebooks/07b_dense_esg_v2_colab.ipynb`).
- C-4 사례분석: DRIVER/BOILER, 상하위 10, Mann-Whitney, 밀도 상관 산출물 발견(`data/processed/08_h2_*.csv`).
- D-1 숫자 밀도: 선택 분석으로 계산 완료(`data/processed/11_defense_number_density.csv`, `data/processed/11_defense_number_density_correlations.csv`).
- D-2/D-3: 이번 실행에서는 시간상 신규 계산하지 않음. D-3은 기존 `data/processed/08_h4_length_sensitivity.csv`와 `07d_a4_length_myth.csv`에 문장 수/문자 수 민감도 일부 존재.
