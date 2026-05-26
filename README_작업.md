
# 흐름

![[Pasted image 20260526145707.png]]

---

### 28(목)까지 정리할것
- [상현]님이 3개 섹션을 왜 사용하는지 근거 찾아주기
- [승준] 전처리 정리 + 그걸로 fasttext후 결과정리 
	- 임계값 설정은 목요일에 자료올림. 서로 어떻게 할지 확인하고 금요일에 확정
		- 노이즈있어도 임계값설정으로 후보군 -> 사람이 검토 
- [연진] Dense embedding 기준문장 cosine 설계 : 
	- 정규화랑,로마숫자제거, 해서 한국어 문장만 남겨서 돌리는거라 TF-IDF랑 달라요(형태소분석x)



---

### 흐름에 대한 코멘트
### 1. 데이터 수집
- 381개 모두 완료
- 보고서 정리필요

### 2. 섹션 구성
- 2,4,6 섹션을 기본으로 사용하기 
	- [상현]님이 3개 섹션을 왜 사용하는지 근거 찾아주기
		- S/G관련 문장이 많다 등등
- 8,11 섹션에 대해서는 [확장]으로 진행할예정
	- "S/G 관련 narrative가 실제로 더 존재하는지 보기 위해 VIII/XI를 추가했다"로 정당화

### 3. 전처리
- 토큰화,불용어,회사명 제거 진행. (실험X 고정)



### 4. 3가지 옵션




---

### 흐름 상세

**1. 데이터 수집** — `stock_code → corp_code`(OpenDART corpCode) → `list.json`으로 `fiscal_year+1`에 공시된 사업보고서 `rcept_no` → `document.xml` ZIP → XML 텍스트. 키는 `stock_code × fiscal_year`, 회사명 merge 금지. 못 찾은 행은 0으로 안 채우고 사유 기록.

**2. 섹션 구성** — core(II·IV·VI) 콘텐츠 맵으로 확정, extended(+VIII·XI)는 robustness. 같은 기업-연도의 추출 문장들을 1 document로 묶어 기업-연도당 1행.

**3. 동일 전처리** — 형태소 분석기 하나 고정(Kiwi 등), 명사 위주 토큰, 불용어 + **회사명·계열사명 제거**(고유명사가 TF-IDF 왜곡). 파이프라인 하나로 고정하고 의사결정 로그에 기록.

**4. Seed TF-IDF + 3×3 교차표** — 성공 기업-연도 document로 TfidfVectorizer fit, seed 30개(E/S/G 10개씩) 컬럼만 골라 차원별 합산. **L2 정규화 벡터 사용**(문서 길이 mechanical 효과 차단). 교차표 = {E·S·G_text} × {E·S·G_grade} 9칸에 Spearman ρ. 대각선만 강하면 차원별 측정 성공, 비대각선도 강하면 공시량 효과 의심.

**5. 확장 TF-IDF — θ 스윕** — II/IV/VI 텍스트로 fastText 직접 학습 → seed별 최근접 후보. cosine 분포를 먼저 보고 θ 그리드 결정(0.3/0.4/0.5 미리 박지 말 것). 각 θ에서 상위 100단어 검토해 후보수·채택·잡음 표. **θ는 사전 품질(잡음률·해석가능성)로만 선택**, ρ는 사후 안정성 확인용. 최종 θ에서 수작업 필터 → expanded dictionary → 같은 방식으로 교차표.

**6. Dense embedding 기준문장 cosine** — E/S/G 기준문장 각 2~3개 패러프레이즈 작성. 한국어 문장 임베딩(multilingual-e5-large-instruct, bge-m3, KR-SBERT 중 하나)으로 기업 document와 기준문장 임베딩 → cosine, 패러프레이즈 평균. TF-IDF cosine 아님(seed 점수와 순환). TF-IDF 피처와 상관 보면 수렴 타당도.

**7. 회귀 — 통제 없/유 비교** — grade 숫자화(S=6…D=0). 주모형 1개 선택(OLS=직관 baseline, ordered logit=서열 보존, A+ binary logit=해석 쉬움). (a) `grade ~ text` 만, (b) `+ log(공시분량) + log(자산) + 업종더미`. **핵심은 (a)→(b)에서 텍스트 계수 변화** — 잔존하면 signal, 소멸하면 분량 교란. 표준화 계수 + VIF 보고.

**8. 메인 렌즈 선택** — "최고 ρ 피처"가 아니라 ① face validity(상위/하위 문장 직접 읽기) ② 3×3 대각선 선명함 ③ 통제 후 안정성, 셋으로 종합 판단. 보통 expanded가 seed OOV를 보완하면 메인, dense는 비교 렌즈. 나머지는 버리지 말고 robustness로 같이 보고.

**9. cheap-talk vs disclosure signal 해석** — ρ가 0.1~0.2면 유의해도 약함, "유의=중요" 금지. 통제 후 효과 잔존 + 대각선만 강 → disclosure signal 쪽. 통제 후 소멸 또는 비대각선까지 강 → cheap-talk(공시 장황함). 결론은 연관성(인과 아님), pilot 표본 한계 명시. 증권사 액션은 **등급-텍스트 괴리 종목 플래그(실사 트리거)**지 등급 대체가 아님.


---

### 기타 문장(나중에 보고서에 작성)

 <임베딩 기반 확장은 ESG relevance가 아닌 일반 semantic/형태 유사성을 함께 포착하므로, threshold 기반 후보군 생성 후 수작업 검토를 통해 최종 확장 사전을 구성하였다.>