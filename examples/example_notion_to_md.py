"""Notion → 마크다운 변환 예시"""
from md_notion_bridge.client import NotionClient
from md_notion_bridge.notion_to_md import convert_page

PAGE_ID = "여기에_페이지_ID_입력"

client = NotionClient()
page = client.get_page(PAGE_ID)
blocks = client.get_block_children(PAGE_ID)
markdown = convert_page(page, blocks)

with open("output.md", "w", encoding="utf-8") as f:
    f.write(markdown)

print("output.md 저장 완료!")
print(markdown[:500])