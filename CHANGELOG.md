# Changelog

모든 변경 사항은 이 파일에 기록됩니다.
[Keep a Changelog](https://keepachangelog.com/ko/1.0.0/) 형식을 따릅니다.

---

## [0.2.0] - 2026-02-20

### 추가

- 테스트 코드 작성 (pytest) — `md_to_notion`, `notion_to_md`, `korean` 유틸 단위 테스트
- GitHub Actions CI 설정 (Python 3.10 / 3.11 / 3.12 멀티버전 자동 테스트)
- H4~H6 제목 지원 (Notion 최대치인 H3으로 자동 변환)
- 중첩 목록 지원 (2단계 들여쓰기)
- 연속 줄 문단 병합 (여러 줄이 하나의 paragraph 블록으로 합쳐짐)
- 표 셀 내 인라인 스타일 지원 (굵게, 기울임 등)
- `pyproject.toml` dev 의존성 그룹 추가 (`pip install -e ".[dev]"`)

### 수정

- 빈 코드블록 안전 처리 (공백 1칸으로 대체)
- 코드블록 들여쓰기 복원 로직 추가 (Notion pull 시 1칸으로 뭉개지던 문제)
- 구분선(`---`) pull 시 뒤따르는 불필요한 빈 줄 제거
- `normalize_punctuation` 줄 시작 들여쓰기 보존 버그 수정
- Notion API 타임아웃 60초로 증가
- `create_page` 블록을 페이지 생성 후 별도 추가하는 방식으로 변경 (타임아웃 방지)
- `append_blocks` 괄호 오타 수정

### 개발

- `.gitignore` 에 `.coverage`, `coverage.xml` 추가

---

## [0.1.0] - 2026-02-20

### 추가

- 마크다운 → Notion 블록 변환기 (`md_to_notion`)
- Notion → 마크다운 역변환기 (`notion_to_md`)
- 블록 타입별 변환 모듈 (코드블록, 표, 이미지)
- 한국어 최적화 유틸 (NFC 정규화, 전각 문장부호 변환, 2000자 자동 분할)
- Notion API 클라이언트 래퍼 (`client.py`)
- 설정 관리 모듈 (`config.py`)
- CLI 인터페이스 (`push` / `pull` / `push-all` / `pull-all`)
- 배치 처리 모듈 (재시도, 속도 제한 대응, 파일 크기 검사)
- 예외 클래스 정의 (`exceptions.py`)
