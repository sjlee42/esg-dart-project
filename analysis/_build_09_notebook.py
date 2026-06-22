"""빌더: notebooks/09_presentation_figures.ipynb 생성.

`analysis/09_presentation_figures.py`(배치 버전)의 그림 함수를 inspect.getsource 로
그대로 가져와 **그림 1개 = 셀 1개**로 배치한 인터랙티브 노트북을 만든다.
- 기존 결과 CSV만 시각화(재분석·재임베딩 없음) — .py 와 동일 코드, 자동 동기.
- 각 셀에서 figsize·폭·여백을 조정해 재실행하면 inline 확인 + png/pdf 저장(잘림 잡기 편함).
- 헬퍼(set_korean_font·save_fig·_despine·PALETTE)는 셀에 인라인(편집 가능), save_fig 는
  pad_inches 로 잘림 여유를 주고 figure 를 닫지 않아 inline 표시됨.

재생성: uv run python analysis/_build_09_notebook.py
"""
import inspect
import importlib.util
from pathlib import Path
import nbformat as nbf

ROOT = Path("/Users/home1/esg-dart-project")
PY = ROOT / "analysis/09_presentation_figures.py"
NB = ROOT / "notebooks/09_presentation_figures.ipynb"

# 배치 버전 모듈을 로드(=getsource 용). __main__ 는 실행되지 않음 → 그림 생성 안 함.
spec = importlib.util.spec_from_file_location("presfig", PY)
presfig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(presfig)

nb = nbf.v4.new_notebook()
C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s): C.append(nbf.v4.new_code_cell(s))

# ───────────────────────────────────────────────────────────── 표지
md(r"""# 발표용 그림 생성 — `09_presentation_figures`

> 15분 발표(`outputs/발표_15분_marp.md`)에 들어가는 그림을 만든다. **기존 결과 CSV만 시각화**한다
> — 재인코딩·재토큰화·회귀 재실행 없음(가드레일). 배치(headless) 버전은
> `analysis/09_presentation_figures.py`, 이 노트북은 **그림 1개 = 셀 1개**로 띄워 두어
> *figsize·폭·여백을 바꿔 재실행 → inline 확인 → png/pdf 저장* 을 반복하기 쉽게 한 것이다.
>
> **출력**: `reports/presentation_figures/{figNN}.png` + `.pdf` (DPI 200, `bbox_inches='tight'`,
> `pad_inches=0.25`로 잘림 여유). **폰트**: Noto Sans KR→Apple SD Gothic Neo→AppleGothic 폴백,
> `axes.unicode_minus=False`(− 글리프 깨짐 방지), `≈/≤` 등은 한글로 대체.
>
> | 셀 | 그림 | 들어갈 슬라이드 | 데이터 |
> |---|---|---|---|
> | fig01 | 설계 흐름도 | 슬4 | (도식) |
> | fig02 | 규모가 먼저(43%) | 슬5 | `07d_a1_hierarchical_r2.csv` |
> | fig03 | 분량 착시 | A4 | `07d_a4_length_myth.csv` |
> | fig04 | 생존 매트릭스(메타발견) | 슬6 | `07d_a3_fullcontrol_coef.csv`·`07d_a3_meta_survival.csv` |
> | fig05 | DRIVER vs BOILER | 슬7 | `08_h2_keyword_density_corr.csv`·`08_h2_top_vs_bottom.csv` |
> | fig06 | TF-IDF vs dense 개념도 | 슬8 | `08_h4_dimension_separation.csv`·`07d_a7_g_convergence.csv` |
> | fig07 | 공시량 대비 등급 사분면 | 슬10 | `07d_synthesis_table.csv`(+`_resid`) |
> | fig08 | 약신호 forest CI | A5/슬11 | `07d_a6_signal_ci.csv` |
>
> **잘림이 보이면**: 해당 셀의 `figsize`를 키우거나, 가장자리 주석의 좌표(예 `fig.text(..., -0.02, ...)`)를
> 안쪽으로 옮기거나, 위 `save_fig`의 `pad_inches`를 늘려 재실행한다.""")

# ───────────────────────────────────────────────────────────── 셋업(헬퍼)
md(r"""## 0. 셋업 — 폰트 · 팔레트 · 저장 헬퍼
아래 헬퍼는 편집 가능하다. `save_fig`는 figure를 **닫지 않아** inline으로 표시되고,
`pad_inches`로 가장자리 잘림 여유를 둔다. (배치 `.py`의 헬퍼와 동일하되 inline용으로 닫지 않음.)""")

code(r'''%matplotlib inline
import os, sys
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, FancyBboxPatch

ROOT = "/Users/home1/esg-dart-project"
DP   = f"{ROOT}/data/processed"
OUT  = f"{ROOT}/reports/presentation_figures"
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, f"{ROOT}/analysis")
from synth_lib import _resid, SIZE_Z, LEN_Z, SECTOR_DUMMIES, INTEG_GRADE   # fig07 잔차 재현용

def set_korean_font():
    cands = ["Noto Sans KR", "Apple SD Gothic Neo", "AppleGothic", "NanumGothic", "Malgun Gothic"]
    avail = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((c for c in cands if c in avail), "AppleGothic")
    plt.rcParams["font.family"] = chosen
    plt.rcParams["axes.unicode_minus"] = False   # − 글리프 깨짐(□) 방지
    return chosen
FONT = set_korean_font(); print("font:", FONT)

# §10.5 팔레트(상수)
P = {
    "dominant": "#34495E",   # 규모/1차 지배
    "control":  "#95A5A6",   # 기타 통제
    "text_weak":"#BDC3C7",   # 텍스트 신호 약
    "signal":   "#2563EB",   # 생존/핵심 신호
    "driver":   "#2A9D8F",   # DRIVER/선택적 실질
    "boiler":   "#C9A227",   # BOILER/의무 형식
    "nonrobust":"#F4A259",   # 비강건
    "null":     "#E3E6E8",   # 비유의/null
    "neg":      "#E15759",   # 음(−) 관계 강조
    "ink":      "#1f2937",
    "muted":    "#6b7280",
}
BODY = (12.0, 6.75)   # 16:9 본문 그림 기본 figsize
DPI = 200

def save_fig(fig, name):
    """png+pdf 저장. figure를 닫지 않아 inline 표시됨. pad_inches로 잘림 여유."""
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/{name}.{ext}", dpi=DPI, bbox_inches="tight",
                    pad_inches=0.25, facecolor="white")
    print("saved", name, "→", OUT)

def _despine(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)
    ax.tick_params(length=0)''')

# ───────────────────────────────────────────────────────────── 그림별 셀(getsource)
FIG_META = [
    ("fig01_design_flow",     "슬4 — 연구 설계 흐름도", "박스+화살표 도식(데이터 없음, 수작업 배치). 칸 위치는 `box(x,y,w,h,...)` 좌표로 조정."),
    ("fig02_size_first",      "슬5 — 규모가 먼저(43%)", "단일 막대 + 43% 대형 주석. 화살표 주석은 `ax.annotate(... xytext=...)` 좌표로 이동."),
    ("fig03_length_myth",     "A4 — 분량 착시 해체",   "before/after 막대. (현재 deck 본문 미사용, A4 또는 슬5 보조용.)"),
    ("fig04_survival_matrix", "슬6 — 생존 매트릭스(메타발견)", "4×3 색 매트릭스 + 하단 메타 띠. 셀 크기는 `Rectangle`·`set_xlim/ylim`로."),
    ("fig05_driver_boiler",   "슬7 — DRIVER vs BOILER", "좌 단어카드 + 우 막대(외부 G등급=진한색 주인공). 하단 캡션이 잘리면 `fig.text(0.5,-0.02,...)`의 y를 올린다."),
    ("fig06_tfidf_vs_dense",  "슬8 — TF-IDF vs dense 개념도", "개념 다이어그램(수작업 배치). 박스/화살표 좌표 0~100 좌표계."),
    ("fig07_quadrant",        "슬10 — 공시량 대비 등급 사분면", "산점도(색=통제 잔차, `_resid`로 재현). 라벨 중립 유지(과대공시·그린워싱 금지)."),
    ("fig08_forest_ci",       "A5/슬11 — 약신호 forest CI", "forest. 우측 CI 라벨이 잘리면 `set_xlim` 상한을 키운다."),
]

for name, title, hint in FIG_META:
    fn = getattr(presfig, name)
    md(f"### {title}\n`{name}` · {hint}\n\n> 셀을 재실행하면 **inline 표시 + `reports/presentation_figures/{name}.png·.pdf` 저장**.")
    src = inspect.getsource(fn).rstrip()
    code(f"{src}\n\n{name}()   # inline 표시 + png/pdf 저장")

# ───────────────────────────────────────────────────────────── 마무리
md(r"""## 9. 일괄 재생성 / 배치
모든 그림을 한 번에(헤드리스) 다시 만들려면 셀 대신 배치 스크립트를 쓴다:

```bash
uv run python analysis/09_presentation_figures.py
```

- 이 노트북과 배치 `.py`의 그림 함수는 **동일 코드**다(이 노트북은 `_build_09_notebook.py`가
  `.py`에서 `getsource`로 가져와 빌드). 함수 본문을 수정했다면 양쪽을 맞춰 두면 좋다.
- 발표 deck(`outputs/발표_15분_marp.md`)은 `../reports/presentation_figures/figNN_*.png`를 참조한다.
- 동반 표: `reports/presentation_figures/README_presentation_figures.md`.""")

nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
nbf.write(nb, str(NB))
print(f"wrote {NB}  ({len(C)} cells)")
