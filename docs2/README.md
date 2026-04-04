---
title: "README"
tags: ""
---
# 티들리위키 빌드 테스트

## 폴더 구조
```
index.html          ← 티들리위키 파일
build.py            ← 빌드 스크립트
docs/               → index.html 에 삽입
│   태그없는파일.md  → 태그 없음
│   └── test/
│       태그있는파일.md      → 태그: test
│       프론트매터테스트.md  → 태그: test 커스텀태그 (프론트매터)
backup/             ← 자동 백업 저장
.vscode/
    tasks.json      ← Ctrl+Shift+B 로 빌드
```

## 사용법
1. index.html ~ index5.html 을 이 폴더에 넣기
2. docs/ ~ docs5/ 에 .md 파일 작성
3. `Ctrl+Shift+B` 실행
