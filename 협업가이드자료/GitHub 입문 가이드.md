# 🐱 GitHub 완전 입문 가이드

> 아무것도 몰라도 OK! Git 설치부터 브랜치까지 한 번에 끝내기

---

## 목차

1. [Git & VS Code 설치](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#1-git--vs-code-%EC%84%A4%EC%B9%98)
2. [VS Code ↔ GitHub 연결하기](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#2-vs-code--github-%EC%97%B0%EA%B2%B0%ED%95%98%EA%B8%B0)
3. [GitHub 초대 수락](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#3-github-%EC%B4%88%EB%8C%80-%EC%88%98%EB%9D%BD)
4. [레포지토리 내 PC로 받기 (Clone)](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#4-%EB%A0%88%ED%8F%AC%EC%A7%80%ED%86%A0%EB%A6%AC-%EB%82%B4-pc%EB%A1%9C-%EB%B0%9B%EA%B8%B0-clone)
5. [브랜치 만들고 작업하기](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#5-%EB%B8%8C%EB%9E%9C%EC%B9%98-%EB%A7%8C%EB%93%A4%EA%B3%A0-%EC%9E%91%EC%97%85%ED%95%98%EA%B8%B0)
6. [변경사항 저장하고 올리기 (Commit & Push)](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#6-%EB%B3%80%EA%B2%BD%EC%82%AC%ED%95%AD-%EC%A0%80%EC%9E%A5%ED%95%98%EA%B3%A0-%EC%98%AC%EB%A6%AC%EA%B8%B0-commit--push)
7. [머지(Merge) 요청하기 (Pull Request)](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#7-%EB%A8%B8%EC%A7%80merge-%EC%9A%94%EC%B2%AD%ED%95%98%EA%B8%B0-pull-request)
8. [자주 쓰는 명령어 모음](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#8-%EC%9E%90%EC%A3%BC-%EC%93%B0%EB%8A%94-%EB%AA%85%EB%A0%B9%EC%96%B4-%EB%AA%A8%EC%9D%8C)
9. [🚨 흔한 오류 & 대처법](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#9--%ED%9D%94%ED%95%9C-%EC%98%A4%EB%A5%98--%EB%8C%80%EC%B2%98%EB%B2%95)

---

## 1. Git & VS Code 설치

### Git 설치

Git은 코드 변경사항을 추적하고 관리하는 도구입니다.

1. [https://git-scm.com](https://git-scm.com/) 접속
2. **Download for Windows** 클릭
3. 설치 파일 실행 → 모든 옵션 **기본값(Next)** 으로 진행
4. 설치 완료 확인:
    - `윈도우 키` → `cmd` 검색 → 명령 프롬프트 실행
    - 아래 명령어 입력:
        
        ```
        git --version
        ```
        
    - `git version 2.xx.x` 같은 숫자가 나오면 성공! ✅

### VS Code 설치 (없다면)

1. [https://code.visualstudio.com](https://code.visualstudio.com/) 접속
2. **Download for Windows** 클릭 후 설치

### Git 사용자 정보 등록 (최초 1회만)

VS Code에서 터미널 열기: ` Ctrl + `` ` ``(백틱)` 또는 상단 메뉴 → Terminal → New Terminal

```bash
git config --global user.name "내 이름"
git config --global user.email "깃허브 가입 이메일"
```

---

## 2. VS Code ↔ GitHub 연결하기

> ⚠️ 이 단계를 빠뜨리면 Clone할 때 **404 오류**가 납니다. 반드시 확인하세요!

### 연결 확인 방법 (먼저 체크!)

VS Code 왼쪽 하단을 보면:

- 사람 아이콘에 **이름이 표시됨** → 이미 연결됨 ✅ → 다음 단계로
- 사람 아이콘에 **아무것도 없거나 `⚠️` 표시** → 연결 필요 → 아래 진행

---

### 방법 A: VS Code 계정 아이콘으로 연결 (가장 쉬움)

1. VS Code 왼쪽 하단 **사람 아이콘** 클릭
2. **"Sign in with GitHub"** 클릭
3. 브라우저가 자동으로 열리면서 GitHub 로그인 페이지 뜸
4. GitHub 아이디/비밀번호로 로그인
5. **"Authorize Visual-Studio-Code"** 버튼 클릭
6. VS Code로 돌아오면 하단에 GitHub 이름 표시됨 ✅

---

### 방법 B: GitHub Pull Requests 확장 프로그램으로 연결

1. VS Code 왼쪽 **확장 프로그램 아이콘** 클릭 (퍼즐 조각 모양, `Ctrl+Shift+X`)
2. 검색창에 `GitHub Pull Requests` 입력
3. Microsoft가 만든 것 설치
4. 설치 후 왼쪽 사이드바에 GitHub 아이콘 생김 → 클릭
5. **"Sign in"** → 브라우저에서 로그인 → 승인

---

### 방법 C: 터미널에서 토큰으로 연결 (위 방법이 안 될 때)

GitHub Personal Access Token(PAT)을 발급받아 연결하는 방법입니다.

**① GitHub에서 토큰 발급**

1. GitHub 로그인 → 우측 상단 프로필 사진 클릭
2. **Settings** → 왼쪽 맨 아래 **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. **Generate new token (classic)** 클릭
5. Note에 이름 입력 (예: `vscode-연결`)
6. **`repo`** 항목 체크 ✅
7. 맨 아래 **Generate token** 클릭
8. 생성된 토큰 복사 (⚠️ 이 화면 벗어나면 다시 못 봄! 반드시 메모장에 저장)

**② VS Code 터미널에서 연결**

```bash
git remote set-url origin https://토큰@github.com/계정명/레포지토리명.git
```

예시:

```bash
git remote set-url origin https://ghp_xxxxxxxxxxxxxx@github.com/팀이름/프로젝트명.git
```

---

### 연결 확인

```bash
git remote -v
```

아래처럼 주소가 나오면 연결 성공 ✅

```
origin  https://github.com/팀이름/프로젝트명.git (fetch)
origin  https://github.com/팀이름/프로젝트명.git (push)
```

---

## 3. GitHub 초대 수락

1. 이메일 받은 편지함 확인
2. GitHub에서 온 초대 메일 열기
3. **"View invitation"** 또는 **"Accept invitation"** 버튼 클릭
4. GitHub 로그인 후 초대 수락 완료 ✅

> 💡 메일이 없다면 → [github.com](https://github.com/) 로그인 후 우측 상단 🔔 알림 아이콘 확인

---

## 4. 레포지토리 내 PC로 받기 (Clone)

**Clone** = 원격 서버(GitHub)에 있는 프로젝트를 내 PC로 복사해 오는 것

### 레포지토리 주소 복사

1. GitHub에서 해당 레포지토리 페이지 접속
2. 초록색 **`<> Code`** 버튼 클릭
3. **HTTPS** 탭 선택
4. 주소 옆 📋 복사 버튼 클릭
    - 주소 예시: `https://github.com/팀이름/프로젝트명.git`

### VS Code에서 Clone 받기

1. VS Code 실행
2. 단축키 `Ctrl + Shift + P` 입력
3. 검색창에 `Git: Clone` 입력 후 선택
4. 복사한 주소 붙여넣기 (`Ctrl + V`) → Enter
5. 폴더 선택 창이 뜨면 저장할 위치 선택 (예: 바탕화면, 문서 폴더 등)
6. 완료 후 **"Open"** 클릭

> ✅ 왼쪽 파일 탐색기에 프로젝트 파일들이 보이면 성공!

---

## 5. 브랜치 만들고 작업하기

### 브랜치(Branch)란?

- **main(또는 master)** = 팀의 최종 완성본이 있는 곳
- **브랜치** = 내가 혼자 작업하는 복사본 공간
- 브랜치에서 작업하면 다른 팀원 작업에 영향을 주지 않아요!

```
main ──────────────────────────── (팀 최종본)
        │
        └── 내브랜치 ── 작업 ── 작업 ── (나만의 작업공간)
```

### 브랜치 만드는 법 (VS Code)

**방법 A: VS Code 하단 바 사용 (쉬움)**

1. VS Code 왼쪽 하단에 `main` 또는 `master` 글자 클릭
2. **"+ Create new branch"** 선택
3. 브랜치 이름 입력 (예: `feature/로그인`, `김철수-작업`)
4. Enter → 자동으로 새 브랜치로 이동됨 ✅

**방법 B: 터미널 사용**

```bash
# 브랜치 만들고 바로 이동
git checkout -b 브랜치이름

# 예시
git checkout -b feature/login
```

> 💡 **브랜치 이름 규칙** (팀마다 다를 수 있음)
> 
> - 영어 소문자, 하이픈(-) 사용 권장
> - 예: `feature/기능명`, `fix/버그명`, `이름/작업내용`

### 현재 브랜치 확인

```bash
git branch
```

- 앞에 `*` 표시된 것이 현재 내가 있는 브랜치

---

## 6. 변경사항 저장하고 올리기 (Commit & Push)

### 용어 정리

|용어|의미|
|---|---|
|**Commit**|변경사항을 로컬(내 PC)에 저장 (저장점 만들기)|
|**Push**|저장된 내용을 GitHub 서버에 올리기|

### VS Code에서 하는 법 (버튼 클릭 방식)

1. 파일 수정 후 왼쪽 사이드바 **소스 제어** 아이콘 클릭 (분기 모양 아이콘)
2. 변경된 파일들이 보임 → `+` 버튼 클릭 (Stage Changes)
3. 상단 메시지 입력창에 작업 내용 입력
    - 예: `로그인 버튼 추가`, `버그 수정`
4. **Commit** 버튼 클릭 (✓ 체크 버튼)
5. **Sync Changes** 또는 **Push** 버튼 클릭 → GitHub에 올라감! ✅

### 터미널에서 하는 법

```bash
# 1. 변경된 파일 전부 스테이징
git add .

# 2. 커밋 (저장점 만들기)
git commit -m "작업 내용을 여기에 작성"

# 3. 내 브랜치를 GitHub에 올리기
git push origin 브랜치이름

# 예시
git push origin feature/login
```

---

## 7. 머지(Merge) 요청하기 (Pull Request)

**Merge** = 내 브랜치 작업을 팀의 main 브랜치에 합치는 것 **Pull Request(PR)** = "내 작업 확인하고 합쳐주세요!" 라고 요청하는 것

### Pull Request 만들기

1. Push 후 GitHub 레포지토리 페이지 접속
2. 상단에 노란 배너가 뜸: **"Compare & pull request"** 버튼 클릭
    - 없다면: **"Pull requests"** 탭 → **"New pull request"** 클릭
3. `base: main` ← `compare: 내브랜치` 확인
4. 제목과 설명 작성 (어떤 작업인지 팀원들이 알 수 있게)
5. **"Create pull request"** 클릭

### 팀원이 승인하면?

- 팀원이 리뷰 후 **Merge** 버튼 클릭 → main에 합쳐짐! ✅
- 이후 로컬에서 main 업데이트:
    
    ```bash
    git checkout maingit pull origin main
    ```
    

---

## 8. 자주 쓰는 명령어 모음

```bash
# 현재 상태 확인
git status

# 브랜치 목록 보기
git branch

# 브랜치 이동
git checkout 브랜치이름

# 최신 내용 받아오기 (다른 팀원 작업 내려받기)
git pull origin main

# 변경사항 스테이징
git add .

# 커밋
git commit -m "작업 내용"

# 푸시
git push origin 브랜치이름
```

---

## 9. 🚨 흔한 오류 & 대처법

---

### ❌ VS Code에서 GitHub 로그인이 안 될 때

**Clone 또는 Push 시 404, 인증 오류가 반복될 때**

```bash
# 현재 저장된 자격증명 삭제 후 재시도
git credential reject
```

또는 Windows라면:

1. `윈도우 키` → **자격 증명 관리자** 검색
2. **Windows 자격 증명** 탭 클릭
3. `github.com` 항목 찾아서 **제거**
4. VS Code에서 다시 Push → 로그인 팝업 뜨면 로그인

> 💡 그래도 안 되면 **방법 C (토큰 방식)** 으로 연결하세요 → [2번 섹션 참고](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#2-vs-code--github-%EC%97%B0%EA%B2%B0%ED%95%98%EA%B8%B0)

---

### ❌ `repository not found` / `404` 오류

**Clone 할 때 또는 Push 할 때 발생**

|원인|대처법|
|---|---|
|**VS Code에 GitHub 로그인 안 됨**|[2번 섹션](https://claude.ai/chat/78874024-3a64-4ce7-986d-4d95bfd760f5#2-vs-code--github-%EC%97%B0%EA%B2%B0%ED%95%98%EA%B8%B0) 참고해서 연결 먼저!|
|초대를 아직 수락 안 함|이메일 또는 GitHub 알림(🔔)에서 초대 수락|
|URL이 잘못됨|GitHub 레포 페이지에서 주소 다시 복사|
|GitHub 자격증명이 오래된 것으로 저장됨|자격 증명 관리자에서 github.com 항목 삭제 후 재시도|

```bash
# 현재 연결된 원격 주소 확인
git remote -v
```

주소가 이상하면:

```bash
git remote set-url origin https://github.com/올바른주소/레포명.git
```

---

### ❌ `Please tell me who you are` 오류

**Commit 할 때 발생 — Git에 이름/이메일 등록이 안 된 것**

```bash
git config --global user.name "내 이름"
git config --global user.email "GitHub 가입 이메일"
```

---

### ❌ `fatal: not a git repository` 오류

**현재 폴더가 Git 프로젝트가 아닐 때 발생**

원인: Clone한 폴더가 아닌 다른 곳에서 명령어를 실행한 것

```bash
# 현재 위치 확인
pwd

# VS Code에서 올바른 폴더를 열었는지 확인
# File > Open Folder → Clone 받은 폴더 선택
```

---

### ❌ `Authentication failed` 오류

**Push 할 때 아이디/비밀번호가 틀렸다고 나올 때**

GitHub는 2021년부터 비밀번호 대신 **Personal Access Token(PAT)** 을 사용해요.

1. GitHub → 우측 상단 프로필 → **Settings**
2. 왼쪽 하단 **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. **Generate new token** 클릭
5. `repo` 항목 체크 → 생성
6. 생성된 토큰을 복사해서 비밀번호 자리에 붙여넣기

> 💡 토큰은 한 번만 보여주니 반드시 메모장에 저장해두세요!

---

### ❌ `rejected` / `failed to push` 오류

**Push 할 때 거부당했을 때**

원인: 다른 팀원이 먼저 올린 내용이 내 로컬에 없는 상태

```bash
# 먼저 최신 내용을 받아오고 나서 Push
git pull origin 브랜치이름
git push origin 브랜치이름
```

> ⚠️ pull 후 충돌(Conflict)이 생기면 아래 충돌 항목 참고

---

### ❌ `CONFLICT` / 충돌(Merge Conflict) 오류

**같은 파일의 같은 부분을 두 명이 동시에 수정했을 때 발생**

VS Code에서 해당 파일을 열면 이런 표시가 생김:

```
<<<<<<< HEAD
내가 수정한 내용
=======
팀원이 수정한 내용
>>>>>>> origin/main
```

**해결 방법:**

1. VS Code가 자동으로 충돌 파일을 표시해줌
2. **"Accept Current Change"** (내 것 유지) 또는 **"Accept Incoming Change"** (팀원 것 유지) 또는 직접 편집
3. 저장 후 다시 Commit & Push

```bash
git add .
git commit -m "충돌 해결"
git push origin 브랜치이름
```

> 💡 충돌은 나쁜 게 아니에요! 팀원과 소통해서 어떤 코드를 살릴지 정하면 돼요.

---

### ❌ `detached HEAD` 상태

**브랜치가 아닌 특정 커밋에 떠 있는 상태 (작업하면 안 됨!)**

```bash
# 다시 브랜치로 돌아가기
git checkout main

# 또는 내 브랜치로
git checkout 내브랜치이름
```

---

### ❌ 커밋 메시지를 잘못 입력했을 때

**가장 최근 커밋 메시지 수정 (Push 전에만 가능)**

```bash
git commit --amend -m "올바른 메시지"
```

---

### ❌ 작업하다가 전부 되돌리고 싶을 때

**수정한 내용을 버리고 마지막 커밋 상태로 되돌리기**

```bash
# 특정 파일만 되돌리기
git checkout -- 파일명.확장자

# 전체 되돌리기 (주의: 복구 불가!)
git reset --hard HEAD
```

> ⚠️ `reset --hard`는 작업 내용이 완전히 사라지니 신중하게 사용하세요!

---

### ❌ `src refspec main does not match any` 오류

**Push할 브랜치가 아직 커밋이 없을 때**

원인: 한 번도 커밋을 안 한 상태에서 Push 시도

```bash
# 먼저 파일을 스테이징하고 커밋부터 하기
git add .
git commit -m "첫 커밋"
git push origin main
```

---

### ❌ VS Code에서 Git 버튼이 안 보일 때

- Git이 설치 안 된 것 → git-scm.com에서 설치 후 VS Code 재시작
- 또는 Clone한 폴더가 아닌 상위 폴더를 열었을 가능성 → `File > Open Folder`로 정확한 폴더 열기

---

## 전체 흐름 요약

```
① Git 설치 & VS Code 설치
        ↓
② GitHub 초대 수락
        ↓
③ 레포지토리 Clone (내 PC로 받기)
        ↓
④ 브랜치 만들기 (내 작업 공간)
        ↓
⑤ 코드 작업하기
        ↓
⑥ Commit & Push (저장 & 올리기)
        ↓
⑦ Pull Request 생성 (합쳐달라고 요청)
        ↓
⑧ 팀원 리뷰 & Merge 완료! 🎉
```

---
