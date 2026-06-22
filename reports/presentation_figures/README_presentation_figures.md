# 발표용 그림 (presentation_figures)

`analysis/09_presentation_figures.py`로 일괄 생성. **기존 결과 CSV만 시각화**(재분석·재임베딩 없음).
폰트 = Apple SD Gothic Neo(폴백 AppleGothic), `axes.unicode_minus=False`로 − 글리프 깨짐 방지.
각 그림 `.png`(발표) + `.pdf`(벡터) 동시 생성, DPI 200, 16:9.

재생성: `uv run python analysis/09_presentation_figures.py`

| 파일 | 목적(메시지 한 줄) | 데이터 출처 | 들어갈 슬라이드 | 조심표현 |
|---|---|---|---|---|
| `fig01_design_flow` | 연구 설계 한눈에: 한 문서→3트랙→등급매칭→통제→회귀 | (도식) | 슬4 데이터·설계 | — |
| `fig02_size_first` | 텍스트보다 먼저, 규모가 등급을 설명(43% vs 텍스트 ≤5%p) | `07d_a1_hierarchical_r2.csv` | 슬5 핵심결과 | "예측/만든다" 금지 → "설명력 증분" |
| `fig03_length_myth` | 분량 자체는 품질 아님 — 길이↔등급의 절반 이상이 규모 경유 | `07d_a4_length_myth.csv` | A4 분량착시 / 슬5 보조 | — |
| `fig04_survival_matrix` | 표현 바꾸면 살아남는 차원이 바뀐다 → 단일 공시충실도 요인(E0/S1/G1) | `07d_a3_fullcontrol_coef.csv`·`07d_a3_meta_survival.csv` | 슬6 메타발견(신설) | "G만 이겼다" 금지 → "seed 기준 G, dense 기준 S" |
| `fig05_driver_boiler` | G에는 회사를 구별하는 선택적 실질어가 있다(DRIVER +0.285/BOILER −0.192) | `08_h2_keyword_density_corr.csv`·`08_h2_top_vs_bottom.csv` | 슬7 왜 seed-G | 밀도=길이 미통제 예시, 본증거 0.38** · 인과 금지(연관) |
| `fig06_tfidf_vs_dense` | 더 정교한 모델이 더 좋은 지표는 아니다(IDF 선택성 미복제) | `08_h4_dimension_separation.csv`·`07d_a7_g_convergence.csv` | 슬8 측정타당성 | "dense 실패" 단정 → "측정타당성 교훈" |
| `fig07_quadrant` | 규모·분량 함께 보면 같은 등급도 다르게 읽힘(통제 잔차) | `07d_synthesis_table.csv`(+`_resid` 재현) | 슬10 시사점B | "과대공시/그린워싱" 금지 → "통제 대비 저평가·탐색적·텍스트로 구별 안 됨" |
| `fig08_forest_ci` | 유의하지만 크지는 않다(seed-G ρ0.17, CI[.04,.30]) | `07d_a6_signal_ci.csv` | 슬11 한계 / A5 | "강한 신호" 금지 → "약신호, 0은 아님" |

## 본문 우선순위 (15분, 본문 4개)
①규모가 먼저(fig02) · ②G 선택적 실질어(fig05) · ③측정법마다 결론 다름(fig04) · ④설계 흐름(fig01).
fig06·fig07·fig08·fig03은 본문 보조 또는 Appendix.

## 검증 체크
- [x] 한글·− 기호 깨짐 없음(8/8 육안 확인, Apple SD Gothic Neo)
- [x] 수치 CSV 일치(규모 43%/.0528, 메타 E0·S1·G1, DRIVER +.285/BOILER −.192, seed-G ρ.17 CI[.04,.30])
- [x] 라벨 중립화(fig07: 과대공시·그린워싱 단어 없음)
