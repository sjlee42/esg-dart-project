"""
fastText 후보의 유사도 임계값별 LLM keep 누적 개수 분석.

사용법:
  python3 scripts/analyze_llm_keep_thresholds.py
  python3 scripts/analyze_llm_keep_thresholds.py --min-threshold 0.4 --step 0.05

출력:
  data/processed/feature_engineering/fasttext_llm_keep_by_seed_threshold.csv
  data/processed/feature_engineering/fasttext_llm_keep_by_dimension_threshold.csv
  data/processed/feature_engineering/fasttext_llm_keep_by_seed_threshold_wide.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_CSV = (
    PROJECT_ROOT
    / "data/processed/feature_engineering/fasttext_seed_candidates_reviewed.csv"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data/processed/feature_engineering"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze absolute llm_keep counts by similarity threshold."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=DEFAULT_INPUT_CSV,
        help="Reviewed candidate CSV with dimension, seed_term, similarity, llm_keep.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where analysis CSVs are written.",
    )
    parser.add_argument(
        "--max-threshold",
        type=float,
        default=0.9,
        help="Highest similarity threshold to test.",
    )
    parser.add_argument(
        "--min-threshold",
        type=float,
        default=0.4,
        help="Lowest similarity threshold to test.",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.1,
        help="Threshold interval. Default makes 0.9, 0.8, 0.7, ...",
    )
    return parser.parse_args()


def make_thresholds(max_threshold: float, min_threshold: float, step: float) -> list[float]:
    if step <= 0:
        raise ValueError("--step must be greater than 0")
    if max_threshold < min_threshold:
        raise ValueError("--max-threshold must be greater than or equal to --min-threshold")

    thresholds: list[float] = []
    current = max_threshold
    while current >= min_threshold - 1e-12:
        thresholds.append(round(current, 10))
        current -= step
    return thresholds


def normalize_llm_keep(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return (
        series.astype("string")
        .str.strip()
        .str.lower()
        .map({"true": True, "false": False})
    )


def summarize_thresholds(
    df: pd.DataFrame,
    group_cols: list[str],
    thresholds: list[float],
) -> pd.DataFrame:
    rows: list[dict] = []

    for group_key, group in df.groupby(group_cols, sort=True, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        previous_candidate_count = 0
        previous_keep_count = 0

        for threshold in thresholds:
            selected = group[group["similarity"] >= threshold]
            candidate_count = len(selected)
            keep_count = int(selected["llm_keep_bool"].sum())
            drop_count = int((selected["llm_keep_bool"] == False).sum())
            unreviewed_count = int(selected["llm_keep_bool"].isna().sum())

            row = dict(zip(group_cols, group_key, strict=True))
            row.update(
                {
                    "threshold": threshold,
                    "candidate_count": candidate_count,
                    "llm_keep_count": keep_count,
                    "llm_drop_count": drop_count,
                    "unreviewed_count": unreviewed_count,
                    "added_candidates_vs_prev_threshold": (
                        candidate_count - previous_candidate_count
                    ),
                    "added_llm_keep_vs_prev_threshold": (
                        keep_count - previous_keep_count
                    ),
                    "llm_keep_rate": (
                        keep_count / candidate_count if candidate_count else 0.0
                    ),
                }
            )
            rows.append(row)

            previous_candidate_count = candidate_count
            previous_keep_count = keep_count

    return pd.DataFrame(rows)


def make_seed_wide_summary(
    by_seed: pd.DataFrame,
    thresholds: list[float],
) -> pd.DataFrame:
    metric_cols = [
        "candidate_count",
        "llm_keep_count",
        "added_llm_keep_vs_prev_threshold",
        "llm_keep_rate",
    ]
    wide = by_seed.pivot(
        index=["dimension", "seed_term"],
        columns="threshold",
        values=metric_cols,
    )
    wide.columns = [
        f"{metric}_ge_{threshold:g}" for metric, threshold in wide.columns.to_flat_index()
    ]
    ordered_cols = ["dimension", "seed_term"]
    for metric in metric_cols:
        ordered_cols.extend(f"{metric}_ge_{threshold:g}" for threshold in thresholds)

    result = wide.reset_index()[ordered_cols]
    count_prefixes = (
        "candidate_count_ge_",
        "llm_keep_count_ge_",
        "added_llm_keep_vs_prev_threshold_ge_",
    )
    count_cols = [
        col for col in result.columns if col.startswith(count_prefixes)
    ]
    result[count_cols] = result[count_cols].astype(int)
    return result


def main() -> None:
    args = parse_args()
    thresholds = make_thresholds(
        args.max_threshold,
        args.min_threshold,
        args.step,
    )

    df = pd.read_csv(args.input_csv, encoding="utf-8-sig")
    required_cols = {"dimension", "seed_term", "candidate", "similarity", "llm_keep"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {sorted(missing_cols)}")

    df = df.copy()
    df["similarity"] = pd.to_numeric(df["similarity"], errors="coerce")
    df["llm_keep_bool"] = normalize_llm_keep(df["llm_keep"])
    df = df.dropna(subset=["similarity"])

    by_seed = summarize_thresholds(
        df,
        group_cols=["dimension", "seed_term"],
        thresholds=thresholds,
    )
    by_dimension = summarize_thresholds(
        df,
        group_cols=["dimension"],
        thresholds=thresholds,
    )
    by_seed_wide = make_seed_wide_summary(by_seed, thresholds)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    by_seed_path = args.output_dir / "fasttext_llm_keep_by_seed_threshold.csv"
    by_dimension_path = (
        args.output_dir / "fasttext_llm_keep_by_dimension_threshold.csv"
    )
    by_seed_wide_path = (
        args.output_dir / "fasttext_llm_keep_by_seed_threshold_wide.csv"
    )

    by_seed.to_csv(by_seed_path, index=False, encoding="utf-8-sig")
    by_dimension.to_csv(by_dimension_path, index=False, encoding="utf-8-sig")
    by_seed_wide.to_csv(by_seed_wide_path, index=False, encoding="utf-8-sig")

    print(f"Input rows: {len(df):,}")
    print(f"Thresholds: {', '.join(f'{t:g}' for t in thresholds)}")
    print(f"Wrote by-seed summary: {by_seed_path}")
    print(f"Wrote by-dimension summary: {by_dimension_path}")
    print(f"Wrote by-seed wide summary: {by_seed_wide_path}")


if __name__ == "__main__":
    main()
