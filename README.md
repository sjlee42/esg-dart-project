# ESG DART 프로젝트

127개 기업 × 3개 사업연도(2022-2024) DART 사업보고서 텍스트 분석

## 환경 세팅

```bash
git clone <이 레포 주소>
cd esg-dart-project
uv sync
```

## API key 설정

`.env.example`을 복사해서 `.env`로 이름 바꾸고, 본인 DART API key를 넣으세요.

```bash
cp .env.example .env
```

## 노트북 실행

```bash
uv run jupyter lab
```

커널은 `Python (esg-dart)` 선택.

## 폴더 구조

- `data/raw/` — DART 원본 사업보고서 (gitignore)
- `data/processed/` — 추출된 ESG 문장, feature 테이블
- `notebooks/` — 분석 노트북 (.ipynb)
- `src/` — 재사용 함수 (전처리, TF-IDF, KoBERT 임베딩)
- `reports/` — 최종 보고서
