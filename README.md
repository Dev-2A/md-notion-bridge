# 🔄️ md-notion-bridge

> 마크다운 ↔ Notion 양방향 변환기

마크다운 파일을 Notion 페이지로 업로드하거나, Notion 페이지를 마크다운 파일로 추출하는 Python CLI 도구입니다.  
표, 코드블록, 이미지 등 복잡한 블록을 지원하며 한국어에 최적화되어 있습니다.

---

## ✨ 주요 기능

- 📤 **마크다운 → Notion**: 로컬 `.md` 파일을 Notion 페이지로 업로드
- 📥 **Notion → 마크다운**: Notion 페이지를 `.md` 파일로 추출
- 📦 **배치 처리**: 디렉토리 단위 일괄 업로드 / 여러 페이지 일괄 추출
- 🧱 **복잡한 블록 지원**: 표, 코드블록, 이미지, 인용문, 할일 목록, 콜아웃 등
- 🇰🇷 **한국어 최적화**: NFC 정규화, 전각 문장부호 변환, 2000자 자동 분할
- 🛡️ **안정적인 에러 핸들링**: API 재시도, 속도 제한 대응, 파일 크기 검사

---

## 📋 지원 블록 타입

| 마크다운 | Notion 블록 |
| --- | --- |
| `# H1` `## H2` `### H3` | heading_1 / 2 / 3 |
| 일반 문단 | paragraph |
| `- 항목` | bulleted_list_item |
| `1. 항목` | numbered_list_item |
| `- [ ]` `- [x]` | to_do |
| `> 인용` | quote |
| ` ``` ` 코드블록 | code |
| `![](url)` | image |
| `\|표\|` | table |
| `---` | divider |
| 콜아웃 (Notion 전용) | → quote 변환 |
| 토글 (Notion 전용) | → 굵은 문단 변환 |

---

## 🚀 설치

### 요구사항

- Python 3.10 이상

### 설치 방법

```bash
git clone https://github.com/Dev-2A/md-notion-bridge.git
cd md-notion-bridge
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .
```

---

## ⚙️ 초기 설정

### 1. Notion Integration 토큰 발급

1. [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations) 접속
2. **New integration** 클릭 → 이름 입력 → Submit
3. 발급된 `secret_xxx...` 토큰 복사
4. 연결할 Notion vpdlwldptj `...` → `Connect to` → 생성한 integration 선택

### 2. `.env` 파일 생성

프로젝트 루트에 `.env` 파일을 생성합니다:

```env
NOTION_API_KEY=secret_여기에_토큰_붙여넣기
NOTION_DEFAULT_PAGE_ID=자주_사용하는_페이지_ID_선택사항
```

---

## 📖 사용법

### 마크다운 → Notion 업로드

```bash
# 기본 업로드
md-notion push README.md --page-id https://notion.so/...

# 제목 직접 지정
md-notion push report.md --page-id abc123 --title "월간 리포트"

# 기본 페이지 ID 설정 시 --page-id 생략 가능
md-notion push guide.md
```

### Notion → 마크다운 추출

```bash
# 파일로 저장 (페이지 제목.md 로 자동 저장)
md-notion pull https://notion.so/...

# 파일명 직접 지정
md-notion pull abc123 --output result.md

# 터미널에 바로 출력
md-notion pull abc123 --stdout
```

### 배치 처리

```bash
# 디렉토리 내 .md 파일 전체 업로드
md-notion push-all ./docs --page-id abc123

# 하위 디렉토리까지 포함
md-notion push-all ./posts --pattern "**/*.md" --page-id abc123

# 여러 Notion 페이지 일괄 추출
md-notion pull-all abc123 def456 ghi789 --output-dir ./exported
```

---

## 🗂️ 프로젝트 구조

```text
md-notion-bridge/
├── md_notion_bridge/
│   ├── __init__.py
│   ├── cli.py              # CLI 진입점
│   ├── client.py           # Notion API 클라이언트
│   ├── config.py           # 설정 관리
│   ├── md_to_notion.py     # 마크다운 → Notion 변환기
│   ├── notion_to_md.py     # Notion → 마크다운 변환기
│   ├── batch.py            # 배치 처리
│   ├── exceptions.py       # 예외 클래스
│   ├── blocks/
│   │   ├── code.py         # 코드블록 변환
│   │   ├── table.py        # 표 변환
│   │   └── image.py        # 이미지 변환
│   └── utils/
│       └── korean.py       # 한국어 최적화 유틸
├── tests/
│   ├── test_md_to_notion.py
│   ├── test_notion_to_md.py
│   └── fixtures/
│       └── sample.md
├── examples/
│   ├── example_md_to_notion.py
│   └── example_notion_to_md.py
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 🔧 Python API로 직접 사용

CLI 없이 코드에서 직접 임포트해서 사용할 수도 있습니다.

```python
from md_notion_bridge.client import NotionClient
from md_notion_bridge.md_to_notion import convert
from md_notion_bridge.notion_to_md import convert_page

# 마크다운 → Notion 블록 변환
blocks = convert("# 안녕하세요\n\n테스트 문단입니다.")

# Notion 클라이언트
client = NotionClient()
page = client.create_page(parent_id="abc123", title="테스트", children=blocks)

# Notion 페이지 → 마크다운
page_data = client.get_page("abc123")
block_data = client.get_block_children("abc123")
markdown = convert_page(page_data, block_data)
print(markdown)
```

---

## ⚠️ 알려진 제한 사항

- Notion 업로드 이미지(`file` 타입)는 URL이 만료될 수 있어 외부 URL로 대체됩니다
- Notion 전용 블록(데이터베이스, 임베드, 북마크 등)은 주석으로 표시됩니다
- 한 페이지당 블록 업로드는 Notion API 특성 상 100개씩 나눠서 처리됩니다
- Notion API 속도 제한(초당 3회)으로 인해 배치 처리 시 요청 간 0.4초 대기합니다

---

## 📄 라이선스

[MIT License](LICENSE)
