# 티들리위키 빌드 시스템

마크다운 파일을 티들리위키 HTML에 자동으로 삽입하는 빌드 시스템이에요.

---

## ⚠️ 시작 전 필수 사항

**`index.html` ~ `index5.html` 파일은 반드시 먼저 레포에 있어야 해요!**
`docs/` 폴더만 있다고 html 파일이 자동 생성되지 않아요.

### 초기 세팅 순서
```
1. 깡통 티들리위키 html 파일 준비 (index.html ~ index5.html, can.html, can5.html)
2. 레포에 html 파일 업로드
3. docs/ ~ docs5/ 폴더에 .md 파일 작성
4. push → 빌드 자동 실행 → 사이트 반영
```

### html 파일 내용 초기화가 필요할 때
```
1. 레포에서 해당 index.html 삭제
2. 해당 docs/ 폴더 삭제
3. can.html 또는 can5.html 을 복사해서 index.html 로 업로드
4. docs/ 폴더에 원하는 .md 파일 작성
5. push → 빌드 자동 실행
```

> docs/ 폴더만 삭제해도 다음 빌드 때 index.html 에 있는 티들러가
> 다시 docs/ 로 내보내지므로 html도 함께 초기화해야 해요.

---

## 📁 폴더 구조

```
hjp8888.github.io/
├── index.html          ← 티들리위키 1번 (블로그)
├── index2.html         ← 티들리위키 2번 (블로그)
├── index3.html         ← 티들리위키 3번 (리뷰)
├── index4.html         ← 티들리위키 4번 (지구)
├── index5.html         ← 티들리위키 5번 (아카이브 🔒)
├── can.html            ← 깡통 html (초기화용 예비)
├── can5.html           ← 깡통 html 비밀번호 버전 (초기화용 예비)
├── build.py            ← 빌드 스크립트
├── .nojekyll           ← Jekyll 비활성화 (필수)
├── backup/             ← 자동 백업 (파일당 최대 2개, 없으면 자동 생성)
├── docs/               → index.html 에 삽입
├── docs2/              → index2.html 에 삽입
├── docs3/              → index3.html 에 삽입
├── docs4/              → index4.html 에 삽입
├── docs5/              → index5.html 에 삽입
│
│   docs 폴더 구조 예시
│   docs/
│   ├── 파일.md              ← 태그 없음 (루트에 바로 넣기)
│   ├── 파일.html            ← 태그 없음 (루트에 바로 넣기)
│   └── 하위폴더/
│       ├── 파일.md          ← 태그: 하위폴더명
│       └── 파일.html        ← 태그: 하위폴더명 (자동 추출)
│
├── img/                ← 이미지 파일
├── .github/
│   └── workflows/
│       └── build.yml   ← GitHub Actions 자동 빌드
└── .vscode/
    └── tasks.json      ← VSCode 로컬 빌드 단축키 (Ctrl+Shift+B)
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

### 태그 규칙

| 작성 방식 | 결과 |
|------|------|
| `tags: "여행 부산"` | 태그 2개: `여행`, `부산` |
| `tags: "[[여행 부산]]"` | 태그 1개: `여행 부산` |
| `tags: "[[여행 부산]] 일상"` | 태그 2개: `여행 부산`, `일상` |

### 구글 검색 링크 최단 형식
```html
<a href="//google.com/search?q=검색어+띄어쓰기" target=_blank>g</a>
```

### 코드 하이라이터

티들리위키 마크다운에서 코드 블록에 언어명을 지정하면 신택스 하이라이팅이 적용돼요.

```javascript
(function(a,b){
    var result = a+b;
    return result;
})(10,20)
```

```css
* { margin: 0; padding: 0; }
html { font-size: 62.5%; }
body { font-size: 14px; }
```

```python
class Singleton:
    __single = None
    def __init__( self ):
        if Singleton.__single:
            raise Singleton.__single
        Singleton.__single = self
```

지원 언어: `javascript` `css` `python` `perl` `html` `bash` `json` 등

---

## 🌐 HTML 파일 지원

`.md` 파일 외에 `.html` 파일도 docs 폴더에 넣으면 티들러로 자동 삽입돼요.

### md vs html 태그 규칙

**md 파일** — 태그는 frontmatter 값만 사용. 폴더 위치는 무관

```
docs/여행/부산/파일.md  (tags: "일기")  →  태그: "일기"   ← frontmatter 우선
docs/여행/부산/파일.md  (tags: "")      →  태그: ""       ← 빈 문자열 그대로
```

**html 파일** — 태그는 폴더 경로에서 자동 추출 (frontmatter 없음)

```
docs/124.html              →  title: "124",    tags: ""
docs/여행/부산/해운대.html  →  title: "해운대",  tags: "여행 부산"
docs/1/2/279.html          →  title: "279",    tags: "1 2"
```

### ZIP 안에 html 파일이 있을 때

ZIP 파일 위치 태그 + ZIP 내부 폴더 태그를 합산해요.

```
docs/html/test.zip
  └── 여행/부산/test.html  →  tags: "html 여행 부산"
  └── test.html            →  tags: "html"

docs/test.zip
  └── 여행/test.html       →  tags: "여행"
```

> ZIP 안의 md 파일은 태그 자동 추출 없이 frontmatter 그대로 사용해요.

### md vs html 우선순위

같은 title의 `.md`와 `.html`이 동시에 있으면 **`.html`이 무조건 덮어씀**

```
docs/서울.md    ← 이게 있어도
docs/서울.html  ← 이게 우선! title·내용·태그 모두 html 기준
```

---

## 🖼️ 이미지 · 파일 삽입

레포 루트에 `img/` 폴더를 만들고 파일을 넣으면 마크다운에서 바로 참조할 수 있어요.

### 이미지

```markdown
![대체텍스트](./img/photo.jpg)
```

지원 형식: `jpg` `png` `gif` `webp` `svg`

크기 조절이 필요하면 HTML을 직접 써요.

```html
<!-- 픽셀 지정 -->
<img src="./img/photo.jpg" width="300">

<!-- 비율 지정 -->
<img src="./img/photo.jpg" style="width:50%">

<!-- 최대 너비 (반응형) -->
<img src="./img/photo.jpg" style="max-width:400px; height:auto">
```

### 영상 · 오디오

```markdown
![](./img/video.mp4)
![](./img/audio.mp3)
```

### PDF

`![]()` 문법으로는 PDF가 표시되지 않아요. 아래 방법을 사용해요.

```html
<!-- 인라인 뷰어 (브라우저에서 바로 표시) -->
<iframe src="./img/document.pdf" width="100%" height="600px"></iframe>
```

### 다운로드 링크

```markdown
[파일명](./img/document.pdf)
```

클릭하면 브라우저 기본 동작 (PDF는 열기, 나머지는 다운로드)

강제 다운로드가 필요하면 HTML을 써요.

```html
<a href="./img/document.pdf" download>PDF 다운로드</a>
<a href="./img/file.zip" download>ZIP 다운로드</a>
```

### 정리

| 파일 종류 | 삽입 방법 | 크기 조절 |
|----------|----------|----------|
| 이미지 (jpg, png 등) | `![](./img/파일)` | `<img width="">` |
| 영상 · 오디오 | `![](./img/파일)` | - |
| PDF 뷰어 | `<iframe src="">` | height 속성으로 조절 |
| 다운로드 링크 | `[이름](./img/파일)` 또는 `<a download>` | - |

---

## ⚙️ 빌드 동작 방식

```
build.py 실행
 ├── 1. backup/ 자동 생성 (없으면) 후 타임스탬프로 html 백업 (파일당 최대 2개)
 ├── 2. docs~docs5 의 모든 .zip 파일 → 임시폴더에 압축 해제
 ├── 3. docs~docs5 의 모든 .md / .html 파일 탐색 (하위폴더 + zip 내부 포함)
 │       ├── .md  → frontmatter title/tags 파싱, type: text/markdown
 │       │          태그는 frontmatter 값만 사용 (폴더 자동 추출 없음)
 │       ├── .html → 파일명이 title, 폴더 경로가 tags, type: text/html
 │       │          태그는 폴더 경로 자동 추출 (zip 위치 + 내부 폴더 합산)
 │       ├── 같은 title이면 .html이 .md를 덮어씀
 │       └── 해당 html에 티들러 방식으로 삽입
 │           ├── 같은 제목 티들러 있으면 → 내용 수정
 │           └── 없으면 → 새 티들러 추가
 ├── 4. html에 있는데 docs에 없는 티들러
 │       └── docs 루트에 .md 파일로 자동 생성 (태그 포함)
 └── 5. index~index5.html 덮어쓰기
```

---

## 🖥️ 사용법

### VSCode Web (github.dev) — 주요 사용 방법

1. `docs/` 폴더에 `.md` 또는 `.html` 파일 작성 또는 수정
2. 소스 컨트롤(`Ctrl+Shift+G`) → 커밋 & 푸시
3. GitHub Actions 자동 실행 → html 업데이트 → Pages 배포
4. `https://hjp8888.github.io` 에서 확인

> 수동 빌드: Actions → 티들리위키 빌드 → Run workflow

### VSCode 설치형 (로컬)

```bash
python build.py   # 빌드
git add .
git commit -m "글 추가"
git push
```

단축키: `Ctrl+Shift+B`

---

## 🔧 GitHub 초기 설정

### Pages 설정
```
레포 → Settings → Pages
→ Source: Deploy from a branch
→ Branch: main / (root) → Save
```

### Actions 권한 설정
```
레포 → Settings → Actions → General
→ Workflow permissions
→ Read and write permissions → Save
```

---

## ⚠️ 주의사항

- `$:/config/AutoSave = no` 설정으로 브라우저 localStorage 자동저장 비활성화
  - GitHub Pages에서 항상 최신 파일 표시
  - 로컬에서 직접 수정 시 `Ctrl+S` 수동 저장 필요
- `backup/` 은 파일당 최대 2개 유지. GitHub git 히스토리가 실질적 백업
- 같은 `title` 의 md 파일이 여러 개면 마지막으로 읽힌 파일로 덮어써짐
- 같은 title의 `.md`와 `.html`이 있으면 `.html`이 우선
- docs/ 폴더만 삭제해도 다음 빌드 때 html에서 다시 내보내지므로 초기화 시 html도 함께 교체 필요

