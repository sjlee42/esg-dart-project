"""빌더: notebooks/10_필요한이미지_생성.ipynb 생성.

`analysis/10_presentation_figures_v2.py`(배치 버전)의 그림 함수를 inspect.getsource 로
그대로 가져와 **그림 1개 = 셀 1개**로 배치한 인터랙티브 노트북을 만든다.
- 기존 결과 CSV만 시각화(재분석·재임베딩 없음) — .py 와 동일 코드, 자동 동기.
- 상단에 한글 폰트 체크 셀(두부 □ 확인) + 셋업(폰트·팔레트·save_fig) 셀.
- save_fig 는 figure 를 닫지 않아 inline 표시되고 png/pdf 저장(잘림 잡기 편함).

재생성: uv run python analysis/_build_10_notebook.py
"""
import inspect
import importlib.util
from pathlib import Path
import nbformat as nbf

ROOT = Path("/Users/home1/esg-dart-project")
PY = ROOT / "analysis/10_presentation_figures_v2.py"
NB = ROOT / "notebooks/10_필요한이미지_생성.ipynb"

# 배치 버전 모듈 로드(=getsource 용). __main__ 미실행 → 그림 생성 안 함.
spec = importlib.util.spec_from_file_location("presfig2", PY)
presfig2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(presfig2)

nb = nbf.v4.new_notebook()
C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s): C.append(nbf.v4.new_code_cell(s))

# ───────────────────────────────────────────────────────────── 표지
md(r"""# 발표자료_v2 핵심 신규 그림 — `10_필요한이미지_생성`

> `outputs/발표자료_v2.md`(14장)의 **슬라이드 6·7·8** 전용 신규 figure를 만든다.
> **기존 결과 CSV만 시각화**한다 — 재인코딩·재토큰화·무거운 임베딩·회귀 재실행 없음(가드레일).
> 배치(headless) 버전은 `analysis/10_presentation_figures_v2.py`, 이 노트북은 그 그림 함수를
> `_build_10_notebook.py`가 `getsource`로 가져와 **그림1개=셀1개**로 띄운 것이다(코드 동일·자동 동기).
>
> **출력**: `reports/presentation_figures/{figNN}.png` + `.pdf` (DPI 200, `bbox_inches='tight'`,
> `pad_inches=0.25`). **폰트**: Noto Sans KR→Apple SD Gothic Neo→AppleGothic 폴백,
> `axes.unicode_minus=False`(− 글리프 깨짐 방지).
>
> | 셀 | 그림 | 슬라이드 | 데이터 |
> |---|---|---|---|
> | fig06 | 4×3 생존 그리드 + PC1 92% 막대 | 슬6 메타발견 | `07d_a3_fullcontrol_coef.csv`·`07d_a3_meta_survival.csv`·`07d_synthesis_table.csv` |
> | fig07 | G 4법 계수(seed만 생존·단어vs의미 역방향) | 슬7 G 해석 | `07d_a3_fullcontrol_coef.csv`·`07d_a7_g_convergence.csv` |
> | fig08b | S·E 계수(S=supervised만·E=0/4) | 슬8 S·E 해석 | `07d_a3_fullcontrol_coef.csv`·`07d_a3_meta_survival.csv` |
>
> **PC1 92% 무결성**: dense supervised 삼중(E_sup·S_sup·G_sup) 주성분의 설명비율(EVR≈0.921)이며
> `종합_기록.md §"③ dense 통합"`의 92%와 일치(다른 컬럼셋은 37~55%로 불일치 → 라벨을 정확히 표기).
>
> **잘림이 보이면**: 해당 셀 `figsize`를 키우거나, 가장자리 텍스트 좌표를 안쪽으로 옮기거나,
> `save_fig`의 `pad_inches`를 늘려 재실행한다.""")

# ───────────────────────────────────────────────────────────── 폰트 체크
md(r"""## 0a. 한글 폰트 체크 — 두부(□)가 보이면 폰트 폴백을 바꿔라
아래 셀을 실행해 한글·마이너스(−)가 정상 렌더되는지 먼저 확인한다.""")

code(r'''%matplotlib inline
import matplotlib.pyplot as plt
from matplotlib import font_manager

cands = ["Noto Sans KR", "Apple SD Gothic Neo", "AppleGothic", "NanumGothic", "Malgun Gothic"]
avail = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((c for c in cands if c in avail), "AppleGothic")
plt.rcParams["font.family"] = FONT
plt.rcParams["axes.unicode_minus"] = False
print("선택 폰트:", FONT)

fig, ax = plt.subplots(figsize=(6.2, 1.2))
ax.text(0.5, 0.5, "한글 확인: 거버넌스·환경·사회 / 음수 −0.06 / 계수 β  (□ 없으면 정상)",
        ha="center", va="center", fontsize=13)
ax.axis("off"); plt.show()''')

# ───────────────────────────────────────────────────────────── 셋업(헬퍼)
md(r"""## 0b. 셋업 — 경로 · 팔레트 · 저장 헬퍼
`save_fig`는 figure를 **닫지 않아** inline 표시되고, `pad_inches`로 가장자리 잘림 여유를 둔다.
(배치 `.py`의 헬퍼와 동일하되 inline용으로 닫지 않음.)""")

code(r'''import os, numpy as np, pandas as pd
from matplotlib.patches import Rectangle

ROOT = "/Users/home1/esg-dart-project"
DP   = f"{ROOT}/data/processed"
OUT  = f"{ROOT}/reports/presentation_figures"
os.makedirs(OUT, exist_ok=True)

# 팔레트(09/10 .py 와 동일) — 생존=채도 높은 파랑, 비유의=옅은 회색(명도·굵기로 구분·색각 고려)
P = {
    "dominant": "#34495E", "control": "#95A5A6", "text_weak": "#BDC3C7",
    "signal": "#2563EB", "driver": "#2A9D8F", "boiler": "#C9A227",
    "nonrobust": "#F4A259", "null": "#E3E6E8", "neg": "#E15759",
    "ink": "#1f2937", "muted": "#6b7280",
}
DPI = 200
REPR_ORDER = ["① seed TF-IDF", "② fastText 확장", "③ dense cosine", "③ dense supervised"]

def save_fig(fig, name):
    """png+pdf 저장. figure를 닫지 않아 inline 표시됨. pad_inches로 잘림 여유."""
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/{name}.{ext}", dpi=DPI, bbox_inches="tight",
                    pad_inches=0.25, facecolor="white")
    print("saved", name, "→", OUT)

def _despine(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)
    ax.tick_params(length=0)

def _is_sig(v):
    return isinstance(v, str) and v.strip() in ("*", "**", "***")''')

# ───────────────────────────────────────────────────────────── 그림별 셀(getsource)
FIG_META = [
    ("fig06_meta_survival", "슬6 — 메타발견(생존 그리드 + PC1 92%)",
     "4×3 색 그리드(생존=파랑) + 우측 PC1 막대. 셀/막대 크기는 `set_xlim/ylim`·`width_ratios`로 조정."),
    ("fig07_g_coef", "슬7 — G 4법 계수(단어 vs 의미)",
     "forest형 계수. seed만 파랑 생존, dense cosine 음(−)은 빨강. 콜아웃이 라벨과 겹치면 `xytext` 이동."),
    ("fig08b_se_coef", "슬8 — S·E 계수(정반대)",
     "좌 S(=supervised만 생존)·우 E(0/4). 노트 박스가 막대와 겹치면 상단 `set_ylim` 여백을 키운다."),
]

for name, title, hint in FIG_META:
    fn = getattr(presfig2, name)
    md(f"### {title}\n`{name}` · {hint}\n\n> 재실행 시 **inline 표시 + `reports/presentation_figures/{name}.png·.pdf` 저장**.")
    src = inspect.getsource(fn).rstrip()
    code(f"{src}\n\n{name}()   # inline 표시 + png/pdf 저장")

# ───────────────────────────────────────────────────────────── 마무리
md(r"""## 일괄 재생성 / 배치
모든 그림을 한 번에(헤드리스) 다시 만들려면 배치 스크립트를 쓴다:

```bash
uv run python analysis/10_presentation_figures_v2.py
```

- 이 노트북과 배치 `.py`의 그림 함수는 **동일 코드**다(이 노트북은 `_build_10_notebook.py`가
  `.py`에서 `getsource`로 가져와 빌드). 함수 본문을 고쳤다면 `uv run python analysis/_build_10_notebook.py`로 재빌드.
- 발표 deck(`outputs/발표자료_v2.md`)은 `../reports/presentation_figures/figNN_*.png`를 참조한다.""")

nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
nbf.write(nb, str(NB))
print(f"wrote {NB}  ({len(C)} cells)")
