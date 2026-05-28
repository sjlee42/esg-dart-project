# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

ESG text analysis pipeline that collects Korean business reports (사업보고서) from OpenDART, preprocesses them, and builds text features (seed TF-IDF, fastText seed expansion, dense embeddings) to compare against KCGS ESG grades. Pilot sample is 127 companies × 3 fiscal years (2022–2024) = 381 company-year documents.

The analytical design (see [README_작업.md](README_작업.md) for the full 9-step flow) is what drives the code, so changes should map back to one of those steps.

## Environment & common commands

Package manager is **uv** (with `uv.lock`) on Python 3.12+. Korean filenames are used throughout — keep UTF-8 paths intact.

```bash
uv sync                                         # install deps from uv.lock
.venv/bin/jupyter notebook                      # open the notebook pipeline
uv run python scripts/llm_filter_candidates.py  # LLM-filter fastText candidates
uv run python main.py                           # placeholder entry point (no real pipeline)
```

Secrets live in `.env` at the project root (gitignored):
- `DART_API_KEY` — OpenDART API key, loaded by notebook 01 and the preprocessing pipeline
- `ANTHROPIC_API_KEY` — used by [scripts/llm_filter_candidates.py](scripts/llm_filter_candidates.py) and notebook `00_기타.ipynb`

There is no test suite, linter config, or build step. Validation happens by re-running notebooks end-to-end.

## Pipeline architecture

The work is staged across numbered notebooks in [notebooks/](notebooks/). Each notebook reads the previous stage's artifact from [data/](data/) and writes the next one — do not reorder.

```
company_master.csv ─► 01_데이터수집 ─► dart_reports/*.json
                                       │
                                       ▼
                     02_데이터탐색 (EDA, no artifact mutation)
                                       │
                                       ▼
                     03_데이터전처리 ─► dart_preprocessed.csv
                                       │
                                       ▼
                     04_피처엔지니어링 ─► feature_engineering/ (fastText model + seed candidates)
                                       │
                                       ▼
              scripts/llm_filter_candidates.py ─► fasttext_seed_candidates_reviewed.csv
              (or 00_기타.ipynb for the same step + threshold analysis)
```

Key cross-cutting decisions:

- **Unit of analysis** is `stock_code × fiscal_year`. The KCGS grade is matched via `esg_year = fiscal_year + 1`. Never merge on `company_name`. Missing rows are recorded with a reason, not zero-filled. (See section 1 of `README_작업.md`.)
- **Section selection**: each DART report JSON has sections `II`, `IV`, `VI` (core, "core(II·IV·VI)") plus `VIII`, `XI` (extended robustness). The preprocessing notebook concatenates these into one `text_raw` per company-year.
- **Preprocessing is fixed, not experimented on** (per `README_작업.md` step 3). The pipeline is: roman-numeral section header removal → `clean_text` (Korean/English only) → Kiwi morphological analysis on `text_raw` (not `text_clean`, because `text_clean` loses word boundaries) → stopword filter from [data/raw/stopwords_ko_esg.txt](data/raw/stopwords_ko_esg.txt) + company/affiliate name removal → POS filter keeping `N*`, `V*`, `SL` (English) tokens.
- **Seed dictionary** lives in [data/raw/seed_dictionary.csv](data/raw/seed_dictionary.csv): 30 seeds (E/S/G × 10) with `pattern` regex-like alternation strings (e.g. `재생에너지|renewable energy`). Each `pattern` is re-tokenized through Kiwi so it lines up with the TF-IDF vocabulary; only patterns that actually appear in vocab are kept.
- **Seed expansion** uses fastText trained on the II/IV/VI corpus (notebook 04). Threshold θ is chosen *post hoc* from candidate quality, not pre-set — see notebook `00_기타.ipynb`, which does LLM-assisted keep/drop labelling, then back-computes per-seed precision curves saved to [reports/figures/](reports/figures/).
- **`reports/03_preprocessing_step5_flow.md`** is the authoritative human-readable explanation of the TF-IDF + seed-scoring stage (notebook 03 section 5 onward). Read it before modifying TF-IDF code.

## LLM filter script specifics

[scripts/llm_filter_candidates.py](scripts/llm_filter_candidates.py) batches fastText candidates per `(dimension, seed_term)` in chunks of 50 and calls `claude-haiku-4-5-20251001` with a fixed ESG criteria prompt. The notebook variant (`00_기타.ipynb`) does the same but additionally checkpoints to `*.checkpoint.jsonl` so a re-run resumes mid-flight. If you add a new filter pass, follow that checkpoint pattern — the run takes a long time and you do not want to redo it.

## Data layout & gitignore caveats

[data/raw/](data/raw/) holds inputs that are versioned (`company_master.csv`, `seed_dictionary.csv`, `stopwords_ko_esg.txt`) plus the cached `CORPCODE.xml` (gitignored by size). [data/processed/](data/processed/) is gitignored entirely (CSVs and large per-company JSONs); regenerate by re-running notebooks 01 and 03. The `.gitignore` whitelists `company_master.csv` but blocks all other `*.csv`, so any new versioned CSV under `data/` needs an explicit `!` rule.
