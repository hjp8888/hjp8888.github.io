---
title: "New Tiddler 1"
tags: ""
---
## 1. 표준 흐름도 (Flowchart)
> 글자 크기 28px와 박스 사이의 간격(2.5배)을 확인하세요.

<div class="mermaid">
graph TD
    Start[4K 모니터 접속] --> Check{가로폭 73%?}
    Check -- "예" --> Success[시원한 화면 출력]
    Check -- "아니오" --> Fix[스타일시트 재확인]
    Success --> End((테스트 완료))
    
    style Start fill:#f9f,stroke:#333,stroke-width:4px
    style End fill:#00ff00,stroke:#333,stroke-width:4px
</div>

---

## 2. 순차도 (Sequence Diagram)
> 텍스트가 겹치지 않고 위아래 여백이 충분한지 확인하세요.

<div class="mermaid">
sequenceDiagram
    사용자->>티들리위키: 텍스트 입력
    티들리위키->>머메이드: 엔진 가동
    머메이드-->>티들리위키: 28px 렌더링
    티들리위키-->>사용자: 결과물 출력
</div>

---

## 3. 간트 차트 (Gantt Chart)
> 가로로 긴 차트에서 글자가 작아지지 않고 스크롤이 생기는지 확인하세요.

<div class="mermaid">
gantt
    title 프로젝트 일정 관리 (28px 고정)
    dateFormat  YYYY-MM-DD
    section 기획단계
    환경 설정           :a1, 2026-04-01, 3d
    스타일 최적화       :after a1  , 5d
    section 실행단계
    데이터 입력         :2026-04-10  , 10d
    최종 검토           : 5d
</div>

---

## 4. 파이 차트 (Pie Chart)
> **중요:** 범례(오른쪽 글자)가 깨지거나 폭탄 아이콘이 뜨지 않는지 확인하세요.

<div class="mermaid">
pie title 티들리위키 활용도
    "지식 정리" : 50
    "프로젝트 관리" : 25
    "일기 및 기록" : 15
    "기타" : 10
</div>