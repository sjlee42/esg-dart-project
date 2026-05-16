# 🛠️ Git 협업 가이드북

> 브랜치 기반 협업 워크플로우 — 작업 시작부터 main 반영까지

---

## 📋 전체 흐름 요약

```
작업 시작 전       →     내 브랜치에서 작업      →     main에 최종 반영     →     반영 후 정리
(최신 상태 동기화)        (커밋 & 푸시)                (PR 또는 머지)               (브랜치 동기화)
```

---

## 1️⃣ 작업 시작 전 — 항상 최신 상태로 맞추기

> ⚠️ 이 단계를 빠뜨리면 나중에 충돌(conflict)이 생길 수 있어요!

```bash
# 1. 내 브랜치로 이동
git checkout sjlee

# 2. 원격 저장소의 최신 변경사항 가져오기
git fetch origin

# 3. main의 최신 내용을 내 브랜치에 반영
git rebase origin/main
# 또는
git merge origin/main
```

**rebase vs merge 차이:**
| | rebase | merge |
|---|---|---|
| 커밋 히스토리 | 깔끔하게 정렬됨 | 머지 커밋이 생김 |
| 추천 상황 | 혼자 작업하는 브랜치 | 여러 명이 같이 쓰는 브랜치 |

---

## 2️⃣ 내 브랜치에만 푸시 — 작업 중 저장

```bash
# 1. 변경된 파일 확인
git status

# 2. 파일 스테이징 (올릴 파일 선택)
git add .                    # 전체 파일
git add 파일명.py             # 특정 파일만

# 3. 커밋 (의미 있는 메시지 작성)
git commit -m "feat: 데이터 탐색 노트북 추가"

# 4. 내 브랜치에 푸시
git push origin sjlee
```

**좋은 커밋 메시지 예시:**
```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
refactor: 코드 리팩토링
chore: 설정 파일 변경
```

---

## 3️⃣ 작업 완료 후 main에 올리기

### 방법 A: GitHub PR 방식 (팀 협업 시 권장 ✅)

```bash
# 1. 최종 커밋 & 푸시
git add .
git commit -m "feat: 최종 작업 완료"
git push origin sjlee
```

이후 GitHub에서:
1. 레포지토리 접속
2. `sjlee` 브랜치 선택 후 **"Compare & pull request"** 클릭
3. base: `main` ← compare: `sjlee` 확인
4. 제목/설명 작성 후 **"Create pull request"**
5. 팀원 리뷰 후 **"Merge pull request"**

---

### 방법 B: 로컬에서 직접 머지 (혼자 작업 시)

```bash
# 1. main으로 이동
git checkout main

# 2. 원격 main 최신화
git pull origin main

# 3. 내 브랜치 머지
git merge sjlee

# 4. main 푸시
git push origin main
```

---

## 4️⃣ main 반영 후 — 내 브랜치 동기화

> main에 올린 뒤 다시 내 브랜치로 돌아와서 최신 상태 맞추기

```bash
# 1. 다시 내 브랜치로 이동
git checkout sjlee

# 2. 반영된 main 내용을 내 브랜치에 적용
git rebase origin/main
# 또는
git merge origin/main

# 3. 강제 푸시 (rebase 사용 시 필요)
git push origin sjlee --force-with-lease
```

---

## ⚠️ 자주 하는 실수 & 조심할 것

### ❌ 절대 하면 안 되는 것

```bash
# main 브랜치에서 직접 작업하고 푸시 — 절대 금지!
git checkout main
git commit -m "작업"
git push origin main   # ❌ 팀 전체에 영향
```

```bash
# force push를 main에 사용 — 절대 금지!
git push origin main --force   # ❌ 다른 사람 커밋 덮어씌워짐
```

---

### ✅ 꼭 지켜야 할 습관

| 상황 | 해야 할 것 |
|---|---|
| 작업 시작 전 | 반드시 `git pull` 또는 `git fetch` + `rebase` |
| 커밋 메시지 | 명확하게 무엇을 했는지 작성 |
| main 머지 전 | 내 브랜치에서 먼저 충돌 해결 |
| 충돌 발생 시 | 혼자 해결 말고 팀원과 확인 후 처리 |
| PR 전 | 내 코드 한 번 더 리뷰 후 올리기 |

---

## 🚨 충돌(Conflict) 발생 시 대처법

```bash
# 충돌 발생하면 아래처럼 표시됨
<<<<<<< HEAD (내 변경사항)
내가 수정한 코드
=======
다른 사람이 수정한 코드
>>>>>>> origin/main
```

**해결 순서:**
1. 충돌 파일 직접 열어서 수정 (원하는 내용만 남기기)
2. `<<<<<<<`, `=======`, `>>>>>>>` 표시 모두 삭제
3. 저장 후:
```bash
git add 충돌파일명
git rebase --continue   # rebase 중이었다면
# 또는
git commit              # merge 중이었다면
```

---

## 📌 자주 쓰는 명령어 한눈에 보기

```bash
git status                    # 현재 상태 확인
git branch                    # 브랜치 목록 확인
git checkout 브랜치명          # 브랜치 이동
git checkout -b 새브랜치명     # 새 브랜치 만들고 이동
git fetch origin              # 원격 변경사항 가져오기 (머지는 안 함)
git pull origin main          # 가져오기 + 머지
git log --oneline --graph     # 커밋 히스토리 시각적으로 보기
git diff                      # 변경사항 확인
git stash                     # 작업 중인 내용 임시 저장
git stash pop                 # 임시 저장한 내용 복원
```

---

## 🔄 전체 워크플로우 한눈에 보기

```
[작업 시작]
    │
    ▼
git checkout sjlee
git fetch origin
git rebase origin/main        ← main 최신 내용 반영
    │
    ▼
[코딩 작업]
    │
    ▼
git add .
git commit -m "메시지"
git push origin sjlee         ← 내 브랜치에만 저장
    │
    ▼
[작업 완료]
    │
    ▼
GitHub PR 생성 → 리뷰 → Merge  ← main 반영
    │
    ▼
git checkout sjlee
git rebase origin/main        ← 내 브랜치도 최신화
```

---

> 📝 **기억할 것:** 항상 **내 브랜치**에서 작업하고, **main은 최종 결과물만** 올라가야 해요!