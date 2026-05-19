# 03_전처리 노트북 5번 이후 코드 흐름 정리

이 문서는 `notebooks/03_전처리.ipynb`의 `## 5. Kiwi 형태소 분석` 이후 코드가 무엇을 계산하는지 정리한 설명 문서입니다.

전체 흐름은 아래와 같습니다.

```text
text_raw 원문
→ Kiwi 형태소 분석
→ 토큰 단위 stopwords 제거
→ TF-IDF matrix 생성
→ 전체 단어 중요도 순위 계산
→ seed_dictionary.csv 기반 E/S/G seed TF-IDF 점수 생성
→ seed 점수 분포 시각화
```

## 5. Kiwi 형태소 분석

이 단계는 `text_raw` 원문을 Kiwi 형태소 분석기에 넣어 토큰으로 분리합니다.

입력은 기업-연도별 보고서 전문입니다.

```python
df["text_raw"]
```

`text_raw`는 앞 단계에서 사업보고서의 `II`, `IV`, `VI` 섹션을 순서대로 합친 텍스트입니다. 즉 한 행은 보통 하나의 기업-연도 문서입니다.

형태소 분석 함수는 다음 역할을 합니다.

```python
def tokenize_with_kiwi(text: str) -> list[str]:
    ...
    return [f"{token.form}/{token.tag}" for token in kiwi.tokenize(text)]
```

결과는 단어와 품사 태그를 함께 저장합니다.

```text
탄소/NNG
중립/NNG
추진/NNG
하다/VV
esg/SL
```

생성되는 주요 컬럼은 다음과 같습니다.

| 컬럼 | 의미 |
|---|---|
| `tokens` | Kiwi 형태소 분석 결과. `단어/품사` 형태의 리스트 |
| `token_count` | 해당 문서의 형태소 토큰 개수 |

중요한 점은 형태소 분석을 `text_clean`이 아니라 `text_raw`에 적용한다는 것입니다. `text_clean`은 한글과 영문만 남기고 전부 이어붙인 텍스트라 단어 경계가 약해질 수 있습니다. 반면 `text_raw`는 원문의 공백과 문장 경계가 남아 있어 Kiwi가 더 자연스럽게 단어를 분리할 수 있습니다.

## 5-1. Stopwords 제거 후 TF-IDF 단어 점수 순위

이 단계는 형태소 분석 결과인 `tokens`에서 분석에 사용할 단어만 남긴 뒤 TF-IDF matrix를 만듭니다.

먼저 불용어 파일을 불러옵니다.

```python
STOPWORDS_PATH = PROJECT_ROOT / "data/raw/stopwords_ko_esg.txt"
```

불용어에는 `및`, `등`, `관련`, `통해`, `사업`, `회사`, `당사`처럼 ESG 의미를 직접 구분하기 어려운 일반 단어가 들어 있습니다.

그다음 `tokens`에서 TF-IDF에 넣을 단어만 고릅니다.

```python
TFIDF_POS_PREFIXES = ("N", "V")
TFIDF_POS_TAGS = {"SL"}
```

현재 남기는 품사는 크게 세 종류입니다.

| 조건 | 의미 |
|---|---|
| `N`으로 시작하는 품사 | 명사 계열 |
| `V`로 시작하는 품사 | 동사/형용사 계열 |
| `SL` | 영문 단어 |

토큰 필터링 과정은 다음 순서입니다.

```text
tokens
→ 단어와 품사 분리
→ 소문자화 및 유니코드 정규화
→ 길이 1 이하 제거
→ stopwords 제거
→ 한글/영문이 아닌 토큰 제거
→ 명사/동사/형용사/영문만 유지
```

이 과정을 거쳐 생성되는 컬럼은 다음과 같습니다.

| 컬럼 | 의미 |
|---|---|
| `tfidf_terms` | TF-IDF에 사용할 정제 토큰 리스트 |
| `tfidf_doc` | `tfidf_terms`를 공백으로 이어 만든 문서 문자열 |

TF-IDF의 문서 단위는 `df`의 행 1개입니다.

```text
문서 1개 = 기업 1개 × 회계연도 1개 사업보고서의 II, IV, VI 합본
```

TF-IDF matrix는 다음 구조입니다.

```text
행 = 기업-연도 문서
열 = 단어
값 = 해당 문서에서 해당 단어의 TF-IDF 점수
```

예를 들면 아래와 같은 구조입니다.

| 문서 | 탄소 | 안전 | 이사회 |
|---|---:|---:|---:|
| 000020_2022 | 0.05 | 0.00 | 0.02 |
| 005930_2024 | 0.18 | 0.04 | 0.09 |

코드에서 핵심 객체는 다음과 같습니다.

| 객체 | 의미 |
|---|---|
| `valid_docs` | TF-IDF에 실제 투입된 비어 있지 않은 문서 |
| `tfidf_matrix` | 문서 × 단어 TF-IDF 행렬 |
| `terms` | TF-IDF matrix의 열 이름, 즉 vocabulary |
| `tfidf_rank` | 단어별 TF-IDF 요약 순위표 |

`tfidf_rank`에는 아래 지표가 들어갑니다.

| 컬럼 | 의미 |
|---|---|
| `term` | 단어 |
| `mean_tfidf` | 전체 문서에서 해당 단어 TF-IDF의 평균 |
| `sum_tfidf` | 전체 문서에서 해당 단어 TF-IDF의 합 |
| `doc_count` | 해당 단어가 등장한 문서 수 |

주의할 점은 TF-IDF 점수는 원래 단어마다 하나가 아니라 `문서 × 단어`마다 하나씩 존재한다는 것입니다. `mean_tfidf`와 `sum_tfidf`는 그 문서별 점수들을 단어 단위로 요약한 값입니다.

분포가 오른쪽으로 긴 단어는 평균이 일부 큰 값에 끌릴 수 있습니다. 따라서 `mean_tfidf`만 보지 말고 `doc_count`, 분포 시각화, median, max 등을 함께 보는 것이 좋습니다.

## 5-2. Seed dictionary 기반 TF-IDF 점수 생성

이 단계는 전체 vocabulary 중에서 `data/raw/seed_dictionary.csv`에 들어 있는 ESG seed 단어만 골라 기업-연도별 E/S/G 점수를 만듭니다.

과제 가이드 기준으로 seed dictionary는 E, S, G 각 10개씩 총 30개 seed term으로 구성되어 있습니다.

예시는 다음과 같습니다.

| dimension | seed_term |
|---|---|
| E | 탄소 |
| E | 온실가스 |
| E | 재생에너지 |
| S | 안전 |
| S | 공급망 |
| G | 이사회 |
| G | 감사위원회 |

이 단계의 핵심 아이디어는 다음과 같습니다.

```text
전체 TF-IDF matrix를 이미 만들었다.
→ 그중 seed dictionary에 해당하는 단어 열만 고른다.
→ seed별 점수를 계산한다.
→ E/S/G 차원별로 seed 점수를 합산한다.
```

먼저 seed term과 pattern을 TF-IDF vocabulary에 맞게 토큰화합니다.

```python
def tokenize_seed_phrase(phrase: str) -> list[str]:
    ...
```

예를 들어 `pattern`이 다음과 같다면:

```text
넷제로|net zero|net-zero
```

각 표현을 Kiwi로 토큰화한 뒤, TF-IDF vocabulary에 실제 존재하는 단어만 남깁니다.

```python
seed_dictionary["tfidf_terms"] = seed_dictionary.apply(expand_seed_pattern, axis=1)
```

이 결과로 seed별로 실제 매칭된 vocabulary를 확인할 수 있습니다.

| 컬럼 | 의미 |
|---|---|
| `tfidf_terms` | 해당 seed가 TF-IDF vocabulary에서 매칭한 단어들 |
| `matched_vocab_count` | 매칭된 단어 수 |

다음으로 seed별 문서 점수를 계산합니다.

```python
scores = tfidf_matrix[:, col_indices].sum(axis=1).A1
```

여기서 `col_indices`는 해당 seed가 매칭한 TF-IDF vocabulary 열입니다.

예를 들어 `온실가스` seed가 `온실가스`, `ghg` 두 단어에 매칭되었다면:

```text
온실가스 seed 점수
= TF-IDF(온실가스) + TF-IDF(ghg)
```

이렇게 만들어지는 객체는 다음과 같습니다.

| 객체 | 의미 |
|---|---|
| `seed_term_scores` | 문서별 seed term 점수 matrix |
| `seed_term_rank` | seed term별 평균, 합계, 등장 문서 수 요약표 |
| `seed_tfidf_features` | 기업-연도별 E/S/G seed TF-IDF feature 표 |

`seed_tfidf_features`에는 차원별 점수가 생성됩니다.

```python
seed_E_tfidf_score
seed_S_tfidf_score
seed_G_tfidf_score
seed_total_tfidf_score
```

현재 seed 가중치는 별도로 주지 않습니다. 모든 seed term은 동일 가중치 1로 합산됩니다.

```text
E score
= 탄소 seed 점수
+ 온실가스 seed 점수
+ 탄소중립 seed 점수
+ ...
```

즉 TF-IDF 자체가 단어 중요도 가중치이고, seed dictionary는 어떤 단어를 ESG 관련 단어로 볼지 정하는 필터 역할을 합니다.

## 5-3. Seed dictionary TF-IDF 상위 20개 단어 점수 분포 시각화

이 단계는 `seed_term_rank`에서 상위 20개 seed term을 골라, 각 seed term의 문서별 TF-IDF 점수 분포를 히스토그램으로 확인합니다.

```python
seed_top_terms = seed_term_rank.head(TOP_N)
```

기본 설정은 다음과 같습니다.

```python
TOP_N = 20
INCLUDE_ZERO_SCORES = False
```

`INCLUDE_ZERO_SCORES = False`는 해당 seed가 등장한 문서의 점수만 분포에 포함한다는 뜻입니다. 즉 seed가 등장하지 않은 문서의 0점은 제외합니다.

만약 전체 문서 기준의 분포를 보고 싶다면 다음처럼 바꿀 수 있습니다.

```python
INCLUDE_ZERO_SCORES = True
```

시각화는 5행 × 4열 subplot으로 만들어집니다.

각 subplot은 하나의 seed term에 대해 다음을 보여줍니다.

| 요소 | 의미 |
|---|---|
| 파란/초록 막대 | 문서별 seed TF-IDF 점수의 빈도 |
| 빨간 선 | 점수 분포를 부드럽게 보여주는 KDE 형태의 곡선 |
| 제목의 `등장 문서 n/N` | 해당 seed가 0보다 큰 점수를 가진 문서 수 |

또한 `seed_tfidf_top20_distribution`이라는 요약표를 만듭니다.

| 컬럼 | 의미 |
|---|---|
| `dimension` | E/S/G 구분 |
| `seed_term` | seed 단어 |
| `doc_count` | 등장 문서 수 |
| `mean` | 등장 문서 기준 평균 점수 |
| `median` | 등장 문서 기준 중앙값 |
| `std` | 표준편차 |
| `min` | 최소값 |
| `max` | 최대값 |

이 분포를 보는 이유는 평균 TF-IDF 점수만으로 seed 중요도를 판단하기 어렵기 때문입니다. 어떤 seed는 대부분의 문서에서 비슷하게 등장하지만, 어떤 seed는 일부 문서에서만 매우 크게 나타납니다. 후자의 경우 평균은 극단값에 영향을 많이 받을 수 있습니다.

## 결과 해석 시 주의점

첫째, `tfidf_rank`는 전체 vocabulary 기준 단어 순위이고, `seed_term_rank`는 seed dictionary에 포함된 단어만 대상으로 한 순위입니다. 두 표의 목적이 다릅니다.

둘째, `seed_E_tfidf_score`, `seed_S_tfidf_score`, `seed_G_tfidf_score`는 ESG 성과를 직접 측정한 값이 아닙니다. 사업보고서에 E/S/G 관련 seed 표현이 얼마나 두드러지게 나타나는지를 측정한 텍스트 feature입니다.

셋째, 점수 분산이 크거나 오른쪽 꼬리가 긴 경우 평균만 쓰면 일부 큰 값에 의해 해석이 흔들릴 수 있습니다. 이런 경우 다음 대안을 함께 검토하는 것이 좋습니다.

```text
log1p 변환 점수
median 점수
상위 k개 seed 평균
seed coverage, 즉 등장 seed 비율
winsorizing 후 평균
```

넷째, 과제 가이드에서는 seed TF-IDF 점수와 ESG 등급의 관계를 바로 회귀로 해석하기 전에 Spearman 순위상관, 등급 그룹 평균 차이 검정, 문장 예시 확인을 권장합니다.

마지막으로, 이 점수들은 인과효과가 아니라 공시 언어와 ESG 등급 사이의 연관성을 보기 위한 설명 변수입니다. 따라서 보고서에서는 "ESG 표현이 강한 기업-연도일수록 등급도 높은 경향이 있는가"처럼 조심스럽게 해석해야 합니다.

