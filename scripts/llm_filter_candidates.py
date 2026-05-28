"""
ESG fastText 후보 단어 LLM 필터링
- fasttext_seed_candidates.csv를 읽어
- seed별 Claude API로 keep/drop 동기 판단
- 결과: fasttext_seed_candidates_reviewed.csv

사용법:
  uv run python scripts/llm_filter_candidates.py

환경변수:
  ANTHROPIC_API_KEY  — .env 파일에 설정 (프로젝트 루트)
"""

import json
import os
from pathlib import Path

import anthropic
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_CSV = PROJECT_ROOT / "data/processed/feature_engineering/fasttext_seed_candidates.csv"
OUTPUT_CSV = PROJECT_ROOT / "data/processed/feature_engineering/fasttext_seed_candidates_reviewed.csv"

MODEL = "claude-haiku-4-5-20251001"
CHUNK_SIZE = 50

ESG_CRITERIA = """[E - Environmental 환경 기준]
- 온실가스 배출 및 기후변화 대응 활동을 수행한다
- 에너지 사용량 절감 및 재생에너지 전환을 추진한다
- 오염물질 배출(대기·수질·토양)을 관리하고 저감한다
- 폐기물 발생을 줄이고 재활용·자원순환을 실천한다
- 물 사용량을 관리하고 수자원을 효율적으로 활용한다
- 생물다양성과 생태계 보전에 기여한다
- 친환경 제품·서비스를 개발하거나 환경경영체계를 운영한다

[S - Social 사회 기준]
- 임직원의 인권을 보호하고 차별을 금지한다
- 안전하고 건강한 근로환경을 제공한다
- 공정한 채용·평가·보상 및 다양성·포용을 보장한다
- 임직원 교육·역량개발 기회를 제공한다
- 협력사와 공정거래 및 동반성장을 실천한다
- 고객의 안전·정보보호·만족을 보장한다
- 지역사회 공헌 및 사회적 책임 활동을 수행한다

[G - Governance 지배구조 기준]
- 이사회의 독립성·전문성·다양성을 확보한다
- 투명한 의사결정 구조와 주주권리를 보호한다
- 윤리경영 및 반부패·준법 체계를 운영한다
- 리스크 관리 및 내부통제 체계를 갖춘다
- 공시·정보공개의 투명성을 확보한다
- 감사기구의 독립성을 보장한다"""

SYSTEM_PROMPT = f"""당신은 ESG(환경·사회·지배구조) 전문 용어 심사 전문가입니다.
fastText 유사도로 추출한 후보 단어가 ESG 보고서에서 해당 seed 개념의 유효한 확장어인지 판단합니다.

ESG 판단 기준:
{ESG_CRITERIA}

판단 규칙:
- keep=true  : seed가 속한 ESG 차원(E/S/G)의 기준에 부합하고, seed 개념과 실질적으로 관련 있는 단어


응답은 반드시 JSON 배열만 출력하세요 (설명 없이):
[{{"word":"단어","keep":true,"reason":"한줄이유"}}, ...]"""


def _load_dotenv() -> None:
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"\'')
        os.environ.setdefault(key, val)


def make_user_message(dim: str, seed: str, candidates: list[str]) -> str:
    dim_label = {
        "E": "Environmental(환경)",
        "S": "Social(사회)",
        "G": "Governance(지배구조)",
    }.get(dim.upper(), dim)
    word_list = "\n".join(f"- {c}" for c in candidates)
    return (
        f"ESG 차원: {dim.upper()} ({dim_label})\n"
        f"Seed 단어: {seed}\n\n"
        f"후보 단어 목록:\n{word_list}"
    )


def parse_response_text(text: str) -> list[dict]:
    text = text.strip()
    if "```" in text:
        for part in text.split("```"):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("["):
                text = part
                break
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def run_filter(df: pd.DataFrame, client: anthropic.Anthropic) -> pd.DataFrame:
    groups = list(df.groupby(["dimension", "seed_term"], sort=False))
    total_chunks = sum(
        (len(g) + CHUNK_SIZE - 1) // CHUNK_SIZE for _, g in groups
    )

    results: dict[tuple, tuple] = {}
    chunk_idx = 0

    for (dim, seed), group in groups:
        candidates = (
            group.sort_values("similarity", ascending=False)["candidate"].tolist()
        )
        for i in range(0, len(candidates), CHUNK_SIZE):
            chunk = candidates[i : i + CHUNK_SIZE]
            chunk_idx += 1
            print(
                f"[{chunk_idx}/{total_chunks}] {dim} / {seed} ({len(chunk)}개)...",
                end=" ",
                flush=True,
            )
            try:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": make_user_message(dim, seed, chunk),
                        }
                    ],
                )
                text = next(
                    (b.text for b in response.content if b.type == "text"), ""
                )
                parsed = parse_response_text(text)
                word_map = {r["word"]: r for r in parsed}
                for cand in chunk:
                    if cand in word_map:
                        r = word_map[cand]
                        results[(dim, seed, cand)] = (
                            r.get("keep"),
                            r.get("reason", ""),
                        )
                keep_n = sum(1 for r in parsed if r.get("keep"))
                print(f"keep={keep_n}/{len(parsed)}")
            except Exception as e:
                print(f"오류: {e}")

    keep_col, reason_col = [], []
    for row in df.itertuples(index=False):
        key = (row.dimension, row.seed_term, row.candidate)
        if key in results:
            k, r = results[key]
            keep_col.append(k)
            reason_col.append(r)
        else:
            keep_col.append(None)
            reason_col.append("")

    df = df.copy()
    df["llm_keep"] = keep_col
    df["llm_reason"] = reason_col
    return df


def main() -> None:
    _load_dotenv()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(".env 또는 환경변수에 ANTHROPIC_API_KEY가 없습니다")

    df = pd.read_csv(SEED_CSV, encoding="utf-8-sig")
    print(f"입력: {len(df):,}행 | seed: {df['seed_term'].nunique()}개")
    print(f"모델: {MODEL}")

    client = anthropic.Anthropic(api_key=api_key)
    result_df = run_filter(df, client)
    result_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    keep_n = result_df["llm_keep"].sum()
    drop_n = (result_df["llm_keep"] == False).sum()
    miss_n = result_df["llm_keep"].isna().sum()
    print(f"\n저장: {OUTPUT_CSV}")
    print(f"  keep=True  : {keep_n:,}개")
    print(f"  keep=False : {drop_n:,}개")
    print(f"  미판정     : {miss_n:,}개")


if __name__ == "__main__":
    main()
