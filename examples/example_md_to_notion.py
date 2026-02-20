"""마크다운 → Notion 변환 예시"""
from md_notion_bridge.client import NotionClient
from md_notion_bridge.md_to_notion import convert

PARENT_PAGE_ID = "여기에_페이지_ID_입력"

markdown = """
# 예시 페이지

## 한국어 텍스트

**굵게**, *기울임*, `인라인 코드`를 지원합니다.

## 표 예시

| 이름 | 역할 |
|------|------|
| 홍길동 | 개발자 |

## 코드블록
```python
print("안녕하세요!")
```
"""

client = NotionClient()
blocks = convert(markdown)
page = client.create_page(PARENT_PAGE_ID, "예시 페이지", children=blocks)
print(f"생성된 페이지: https://www.notion.so/{page['id'].replace('-', '')}")