---
title: "ESG DART 데이터 수집 가이드"
date: 2026-05-04
tags:
  - course/UD
  - project/esg-dart
aliases:
  - "ESG DART data collection guide"
---

> 이 문서를 읽기 전에 `01_assignment_overview.md`에서 전체 흐름을 먼저 확인하세요.

> 이전 단계: `01_assignment_overview.md`에서 전체 흐름 확인 | 다음 단계: `03_minimal_analysis_example.md`에서 분석 방법 확인

# ESG DART 데이터 수집 가이드

텍스트를 분석하려면 먼저 어떤 기업이 어떤 보고서를 제출했는지 파악하고, 그 보고서에서 ESG 관련 문단을 찾아야 합니다.
- `01_assignment_overview.md`에서 확인했듯이, 우리가 찾는 내용은 사업보고서의 II, IV, VI 섹션에 담긴 ESG 관련 표현입니다. 
- MCP, skill, OpenDART API, CLI 등 사용할 수 있는 경로로 `stock_code`에서 `corp_code`를 확인하고, 그 `corp_code`로 사업보고서 `rcept_no`를 찾습니다. 최종 제출에서는 수집하지 못한 행이 있으면 보고서에 이유를 적습니다.

## 먼저 이해할 세 가지 식별자

수집을 시작하기 전에 아래 세 코드를 구분합니다.

| 코드           | 예시               | 역할                                          |
| ------------ | ---------------- | ------------------------------------------- |
| `stock_code` | `005930`         | 기업 식별. `company_master.csv`와 KCGS 등급 연결에 사용 |
| `corp_code`  | `00126380`       | OpenDART 내부 회사 코드. API 조회의 출발점              |
| `rcept_no`   | `20250311001085` | 특정 사업보고서의 접수번호. 원문과 viewer URL로 연결          |

`company_master.csv`에는 이미 `stock_code`가 들어 있습니다. 
- `corp_code`와 `rcept_no`는 CSV에 의도적으로 비어 있으며, 
- MCP, skill, OpenDART API, CLI 등으로 `stock_code`에서 조회해 채웁니다.

> **분석 단위 주의** — 이 과제의 표본 단위는 회사명(`company_name`)이 아니라 `stock_code × fiscal_year`입니다. 같은 종목코드가 사명변경, 분할, 존속회사 표기 차이로 여러 이름으로 나타날 수 있어 (`company_name` 133개 ≠ `stock_code` 127개), join/merge의 기본 키를 회사명으로 두면 silent 오매칭이 발생합니다.

이 과제의 시간 기준은 **KCGS 평가연도 `t`와 직전 회계연도 `t-1` 사업보고서의 연결**입니다.
- 즉 `esg_year = fiscal_year + 1`로 맞추며, 
- 예를 들어 2025년 ESG 등급은 2024.12 사업보고서의 공시 언어와 비교합니다. 
  > 이 설계는 인과관계 식별을 의미하지 않습니다.
- `company_master.csv`의 `esg_grade`, `e_grade`, `s_grade`, `g_grade`는 모두 `esg_year` 기준 KCGS 등급입니다 (`fiscal_year` 기준이 아닙니다).

## MCP로 접수번호 찾기 (연습 경로; 예시)

아래 요청은 삼성전자 예시로 절차를 이해하는 연습입니다. 최종 381개 기업-연도 제출에서는 같은 원칙을 전체 행에 반복합니다.

```text
korean-dart MCP 요청:

company_master.csv의 한 행을 기준으로 사업보고서를 찾아줘.

입력:
- company_name = 삼성전자
- stock_code = 005930
- fiscal_year = 2024
- report type = 사업보고서(A001)

조건:
- stock_code로 corp_code를 먼저 확인
- `corp_code`로 fiscal_year + 1년에 공시된 사업보고서를 찾고, 보고서명과 대상 회계기간이 입력한 `fiscal_year`와 맞는 행을 선택
- 선택한 rcept_no와 rcept_dt를 반환
- DART viewer URL도 같이 반환

반환 column:
company_name, stock_code, corp_code, fiscal_year, report_nm, rcept_no, rcept_dt, viewer_url
```

MCP가 반환한 `rcept_no`와 `viewer_url`을 노트북 표에 기록합니다. viewer URL로 실제 보고서를 열어 내용을 확인하는 것을 권장합니다.

예를 들어 `fiscal_year=2024`라면 공시 검색 범위는 2025년이지만, 선택 기준은 제출 월이 아니라 보고서명과 대상 기간입니다. `사업보고서 (2024.12)`처럼 대상 회계연도가 맞는 보고서를 고르고, 정정공시가 있으면 어떤 접수번호를 사용했는지 기록합니다.

## MCP로 ESG 문단 추출하기 (예시)

접수번호를 찾았다면, 아래 요청으로 ESG 관련 문단 후보를 찾습니다.

```text
korean-dart MCP 요청:

rcept_no=20250311001085 사업보고서 원문에서
ESG 관련 passage 후보를 찾아줘.

찾을 영역:
- 환경(E): 온실가스, 탄소, 재생에너지, 배출량, 감축
- 사회(S): 안전보건, 근로자, 공급망, 협력사
- 지배구조(G): 이사회, 감사위원회, 내부통제, 윤리경영

반환 column:
section, passage, dimension, matched_terms, why_selected
```

MCP가 표를 만들어 주더라도 그대로 끝내지 않습니다. 
- 노트북에서 `section`과 `passage`를 확인하고 passage 후보만 필터링합니다. 
- 최대 381개 기업-연도에서 수집을 시도하고, 수집하지 못한 행은 보고서에 이유를 적습니다.

> ⚠️ **주의**: MCP passage extraction은 DART 원문을 직접 파싱하지 않습니다. LLM이 생성한 passage는 실제 공시 내용과 다를 수 있으므로, 반드시 코드(Python)로 재현하고 viewer URL로 원문 확인하세요.

## 연습 체크포인트

처음에는 **1-2개 기업-연도(firm-years)** 만 골라 연습합니다. 
- 이 단계의 목적은 전체 수집을 끝내는 것이 아니라, 
- 내가 올바른 DART 사업보고서를 찾고 `rcept_no`를 정확히 기록할 수 있는지 확인하는 것입니다.

연습 표에는 최소한 아래 열을 포함하세요.

| 열                                     | 내용                                                                                    |
| ------------------------------------- | ------------------------------------------------------------------------------------- |
| `stock_code`                          | 종목코드                                                                                  |
| `corp_code`                           | OpenDART 내부 회사 코드                                                                     |
| `esg_year`                            | KCGS 평가연도. CSV에서 사용하는 열 이름                                                            |
| `fiscal_year` | 사업보고서 회계연도. `esg_year = fiscal_year + 1` |
| `rcept_no`                            | 사업보고서 접수번호                                                                            |
| `rcept_dt`                            | 사업보고서 접수일                                                                             |

주의: **1-2개 기업-연도 연습은 최종 수집 완료 기준이 아닙니다.** 표의 형식과 DART 보고서 확인 절차를 점검한 뒤, 아래 최종 제출 전 체크포인트 기준으로 확장해야 합니다.

## 최종 제출 전 체크포인트

최종 제출 전에는 `company_master.csv` 기준 **최대 127개 기업 × 3개 평가연도 = 381개 기업-연도(firm-years)** 를 기준으로 점검합니다. 
- 이 단계의 목적은 데이터가 어디에서 왔는지(lineage)를 설명할 수 있고, 
- 누락 또는 수집 실패가 있을 때 그 이유를 최종 보고서에 설명하는 것입니다.

별도 산출물을 만들 필요는 없습니다. 노트북에서 분석에 필요한 식별자를 확인할 수 있으면 됩니다.

모든 팀은 최대 381행을 기준으로 수집을 시도합니다.

노트북에서 확인할 기본 식별자입니다.

| 열               | 내용                                      |
| --------------- | --------------------------------------- |
| `company_name`  | 기업 이름                                   |
| `stock_code`    | 종목코드                                    |
| `corp_code`     | OpenDART 내부 회사 코드                       |
| `esg_year`      | KCGS 평가연도. `esg_year = fiscal_year + 1` |
| `fiscal_year`   | 사업보고서 회계연도                              |
| `rcept_no`      | 사업보고서 접수번호                              |
| `rcept_dt`      | 사업보고서 접수일                               |
| `viewer_url`    | DART viewer URL                         |
| `section`       | 문단이 나온 섹션 (II, IV, VI 중 하나)             |
| `passage`       | 실제 추출한 문장 또는 문단                         |
| `dimension`     | E, S, G 또는 관련 구분                        |
| `matched_terms` | ESG 문단으로 판단한 핵심 용어                      |

최종 제출 전 점검:
- [ ] company_master.csv 기준 최대 381개 기업-연도에서 수집을 시도했다
- [ ] 각 행에 KCGS 평가연도와 직전 회계연도 사업보고서를 연결했다
- [ ] 성공 행은 rcept_no, rcept_dt, viewer_url, ESG passage를 기록했다
- [ ] 수집하지 못한 행이 있으면 최종 보고서에 이유를 적었다


## 전체 분석 흐름

데이터 수집부터 분석까지 전체 단계입니다. 각 단계에서 어떤 선택을 했고 왜 그랬는지를 보고서에 남깁니다.

1. `stock_code`로 `corp_code`를 찾는다.
2. `corp_code`로 OpenDART `list.json` 또는 MCP를 조회해 해당 회계연도의 사업보고서 `rcept_no`를 찾는다.
3. OpenDART `document.xml`로 raw ZIP을 저장한다.
4. XML에서 텍스트를 추출한다.
5. II, IV, VI 섹션을 발췌한다.
6. ESG passage를 추출한다.
7. 형태소 분석기로 한국어를 토큰화한다.
8. 불용어를 제거한다.
9. seed dictionary와 TF-IDF feature를 만든다.
10. fastText로 seed 주변 후보 단어를 찾는다.
11. 후보 단어를 검토한다. fastText 결과를 그대로 ESG 사전으로 확정하지 않는다.
12. 재무통제변수를 붙인다 (선택).
13. OLS 또는 logit 계열로 결과를 확인한다.
14. 실패·결측 행이 있으면 최종 보고서에 설명한다.

중요한 규칙:

- company_master.csv의 최대 381행에서 시작합니다.
- 분석 corpus와 회귀 패널은 수집·추출에 성공한 행으로 만들고, 수집 불가 행은 최종 보고서에 이유를 적습니다.
- 실패 행을 가짜 0으로 채워 텍스트 분석에 넣지 않습니다.

## 재현 가능한 최종 수집 경로

최대 381개 기업-연도 수집은 MCP, skill, OpenDART API, CLI 등으로 찾은 `corp_code`와 `rcept_no`를 노트북 표에 기록하고, 가능한 방식으로 재현성을 보강합니다. 핵심은 특정 도구 하나가 아니라, 어떤 식별자를 어떤 근거로 연결했는지 남기는 것입니다.

### CLI로 수집하기 (예시)

공시 목록을 파일로 저장합니다.

```bash
cd <UD_26_ROOT>

uv run dart-fss disclosure list \
  --corp "00126380" \
  --from 20250101 \
  --to 20251231 \
  --type A \
  --count 100 \
  --pretty \
  --output outputs/samsung_2025_regular_filings.json
```

저장된 파일에서 `사업보고서 (2024.12)` 행의 `rcept_no`를 확인합니다.

재무계정은 아래처럼 받습니다.

```bash
cd <UD_26_ROOT>

uv run dart-fss financial single-account \
  --corp "00126380" \
  --year 2024 \
  --quarter annual \
  --pretty \
  --output outputs/samsung_2024_single_account.json
```

여러 기업-연도로 확장할 때는 파일 이름에 `stock_code`와 `fiscal_year`를 넣습니다.

### 직접 API로 수집하기

최종 production 기준에서는 직접 API 또는 이를 감싼 script가 가장 재현성이 높습니다.

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENDART_API_KEY") or os.getenv("DART_API_KEY")

params = {
    "crtfc_key": api_key,
    "corp_code": "00126380",
    "bgn_de": "20250101",
    "end_de": "20251231",
    "last_reprt_at": "Y",
    "pblntf_detail_ty": "A001",
    "page_count": "100",
}

res = requests.get(
    "https://opendart.fss.or.kr/api/list.json",
    params=params,
    timeout=20,
)
payload = res.json()

rows = payload.get("list", [])
annual_2024 = [
    row for row in rows
    if "사업보고서" in row.get("report_nm", "")
    and "(2024.12)" in row.get("report_nm", "")
]

annual_2024[0]["rcept_no"]
```

원문 zip은 `document.xml`로 받습니다.

```python
import zipfile
from io import BytesIO

params = {
    "crtfc_key": api_key,
    "rcept_no": "20250311001085",
}

res = requests.get(
    "https://opendart.fss.or.kr/api/document.xml",
    params=params,
    timeout=30,
)
res.raise_for_status()

with zipfile.ZipFile(BytesIO(res.content)) as zf:
    first_name = zf.namelist()[0]
    xml_text = zf.read(first_name).decode("utf-8", errors="ignore")

xml_text[:1000]
```

### 재무비율 계산 방식 (예시)

강의 예시는 계산 절차를 확인하기 위한 힌트입니다. 최종 제출에서는 381개 기업-연도에 대해 필요한 재무항목을 직접 확인하고, 사용한 출처와 계산식을 남깁니다.

```text
leverage = total_liabilities / total_assets
roa = net_income / total_assets
profit_margin = net_income / sales
operating_margin = operating_income / sales
```

필요한 항목을 찾지 못한 경우에는 값을 임의로 채우지 말고 최종 보고서에 이유를 적습니다.
