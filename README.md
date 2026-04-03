# 티들리위키 빌드 시스템

마크다운 파일을 티들리위키 HTML에 자동으로 삽입하는 빌드 시스템이에요.

---

## 📁 폴더 구조

```
username.github.io/
├── index.html          ← 티들리위키 1번
├── index2.html         ← 티들리위키 2번
├── index3.html         ← 티들리위키 3번
├── index4.html         ← 티들리위키 4번
├── index5.html         ← 티들리위키 5번
├── build.py            ← 빌드 스크립트
├── .nojekyll           ← Jekyll 비활성화 (필수)
├── backup/             ← 자동 백업 저장 (빌드할 때마다 생성, 없으면 자동 생성)
├── docs/               → index.html 에 삽입
├── docs2/              → index2.html 에 삽입
├── docs3/              → index3.html 에 삽입
├── docs4/              → index4.html 에 삽입
├── docs5/              → index5.html 에 삽입
│
│   docs 폴더 구조 예시 (docs2~docs5 동일)
│   docs/
│   ├── 태그없는파일.md        ← 태그 없음 (루트에 바로 넣기)
│   └── 하위폴더/
│       └── 파일.md           ← 태그: 하위폴더명
│
└── .github/
    └── workflows/
        └── build.yml   ← GitHub Actions 자동 빌드
```

---

## 📝 마크다운 파일 양식

```markdown
---
title: "티들러 제목"
tags: "태그명"
---

## 본문 내용

마크다운 형식으로 자유롭게 작성
```

- `title` — 티들리위키에서 보이는 제목. 생략하면 파일명이 제목이 됨
- `tags` — 티들리위키 태그. 생략하면 태그 없음
- 프론트매터(`---`) 자체를 생략해도 됨

---

## ⚙️ 빌드 동작 방식

```
build.py 실행
 ├── 1. backup/ 자동 생성 (없으면) 후 타임스탬프로 5개 html 백업
 ├── 2. docs~docs5 의 모든 .md 파일 탐색 (하위폴더 포함)
 │       ├── 프론트매터 title/tags 파싱
 │       └── 해당 html에 티들러 방식으로 삽입
 │           ├── 같은 제목 티들러 있으면 → 내용 수정
 │           └── 없으면 → 새 티들러 추가
 ├── 3. html에 있는데 docs에 없는 티들러
 │       └── docs 루트에 .md 파일로 자동 생성
 └── 4. index~index5.html 덮어쓰기
```

---

## 🖥️ 사용법

### VSCode (설치형) 사용 시

1. 레포 클론
```bash
git clone https://github.com/username/username.github.io
cd username.github.io
```

2. `docs/` 폴더에 `.md` 파일 작성

3. 빌드 실행
```bash
python build.py
```

4. 변경사항 푸시
```bash
git add .
git commit -m "글 추가"
git push
```

---

### 파이썬만 설치되어 있을 때

1. 파이썬 설치 확인
```bash
python --version
```

2. `docs/` 폴더에 `.md` 파일 작성

3. 빌드 실행
```bash
python build.py
```

4. 변경사항 푸시
```bash
git add .
git commit -m "글 추가"
git push
```

---

### VSCode Web (github.dev) 사용 시

터미널·파이썬 실행 불가능하므로 **GitHub Actions** 으로 자동 빌드돼요.

1. `github.dev` 에서 `docs/` 폴더에 `.md` 파일 작성

2. 소스 컨트롤(`Ctrl+Shift+G`) → 커밋 & 푸시

3. GitHub Actions 가 자동으로 `build.py` 실행 후 html 업데이트

4. `https://username.github.io` 에서 확인

> Actions 탭에서 빌드 진행상황 확인 가능
> 수동 빌드: Actions → 티들리위키 빌드 → Run workflow

---

## 🔧 GitHub 초기 설정

### Pages 설정
```
레포 → Settings → Pages
→ Source: Deploy from a branch
→ Branch: main / (root)
→ Save
```

### Actions 권한 설정
```
레포 → Settings → Actions → General
→ Workflow permissions
→ Read and write permissions 선택
→ Save
```

---

## ⚠️ 주의사항

- `backup/` 폴더는 빌드할 때마다 쌓이므로 주기적으로 정리 필요 (GitHub이 git 히스토리로 버전관리 해줌)
- 같은 `title` 의 md 파일이 여러 개 있으면 마지막으로 읽힌 파일로 덮어써짐
- `.nojekyll` 파일이 없으면 GitHub Pages가 Jekyll로 빌드해서 오작동할 수 있음
