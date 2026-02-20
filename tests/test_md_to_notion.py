"""마크다운 → Notion 변환기 테스트"""
from __future__ import annotations

import pytest
from md_notion_bridge.md_to_notion import convert, parse_inline


# ------------------------------------------------------------------ #
# parse_inline 테스트
# ------------------------------------------------------------------ #

class TestParseInline:

    def test_plain_text(self):
        result = parse_inline("안녕하세요")
        assert len(result) == 1
        assert result[0]["text"]["content"] == "안녕하세요"

    def test_bold(self):
        result = parse_inline("**굵게**")
        bold = next(r for r in result if r["text"]["content"] == "굵게")
        assert bold["annotations"]["bold"] is True

    def test_italic(self):
        result = parse_inline("*기울임*")
        italic = next(r for r in result if r["text"]["content"] == "기울임")
        assert italic["annotations"]["italic"] is True

    def test_strikethrough(self):
        result = parse_inline("~~취소선~~")
        strike = next(r for r in result if r["text"]["content"] == "취소선")
        assert strike["annotations"]["strikethrough"] is True

    def test_inline_code(self):
        result = parse_inline("`코드`")
        code = next(r for r in result if r["text"]["content"] == "코드")
        assert code["annotations"]["code"] is True

    def test_link(self):
        result = parse_inline("[링크](https://example.com)")
        link = next(r for r in result if r["text"]["content"] == "링크")
        assert link["text"]["link"]["url"] == "https://example.com"

    def test_mixed(self):
        result = parse_inline("일반 **굵게** 일반")
        contents = [r["text"]["content"] for r in result]
        assert "굵게" in contents
        assert "일반 " in contents


# ------------------------------------------------------------------ #
# convert 테스트
# ------------------------------------------------------------------ #

class TestConvert:

    def test_heading1(self):
        blocks = convert("# 제목")
        assert blocks[0]["type"] == "heading_1"
        assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "제목"

    def test_heading2(self):
        blocks = convert("## 소제목")
        assert blocks[0]["type"] == "heading_2"

    def test_heading3(self):
        blocks = convert("### 소소제목")
        assert blocks[0]["type"] == "heading_3"

    def test_paragraph(self):
        blocks = convert("일반 문단입니다.")
        assert blocks[0]["type"] == "paragraph"
        assert blocks[0]["paragraph"]["rich_text"][0]["text"]["content"] == "일반 문단입니다."

    def test_bulleted_list(self):
        blocks = convert("- 항목 하나\n- 항목 둘")
        assert blocks[0]["type"] == "bulleted_list_item"
        assert blocks[1]["type"] == "bulleted_list_item"

    def test_numbered_list(self):
        blocks = convert("1. 첫 번째\n2. 두 번째")
        assert blocks[0]["type"] == "numbered_list_item"
        assert blocks[1]["type"] == "numbered_list_item"

    def test_quote(self):
        blocks = convert("> 인용문입니다.")
        assert blocks[0]["type"] == "quote"
        assert blocks[0]["quote"]["rich_text"][0]["text"]["content"] == "인용문입니다."

    def test_divider(self):
        blocks = convert("---")
        assert blocks[0]["type"] == "divider"

    def test_code_block(self):
        blocks = convert("```python\nprint('hello')\n```")
        assert blocks[0]["type"] == "code"
        assert blocks[0]["code"]["language"] == "python"
        assert "print('hello')" in blocks[0]["code"]["rich_text"][0]["text"]["content"]

    def test_code_block_unsupported_language(self):
        """지원하지 않는 언어는 plain text로 대체"""
        blocks = convert("```unknownlang\ncode\n```")
        assert blocks[0]["code"]["language"] == "plain text"

    def test_image(self):
        blocks = convert("![캡션](https://example.com/img.png)")
        assert blocks[0]["type"] == "image"
        assert blocks[0]["image"]["external"]["url"] == "https://example.com/img.png"

    def test_table(self):
        md = "| 이름 | 나이 |\n|------|------|\n| 홍길동 | 30 |"
        blocks = convert(md)
        assert blocks[0]["type"] == "table"
        assert blocks[0]["table"]["has_column_header"] is True

    def test_empty_string(self):
        blocks = convert("")
        assert blocks == []

    def test_blank_lines_skipped(self):
        blocks = convert("\n\n\n")
        assert blocks == []

    def test_korean_text(self):
        blocks = convert("# 한국어 제목\n\n한국어 문단입니다.")
        assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "한국어 제목"
        assert blocks[1]["paragraph"]["rich_text"][0]["text"]["content"] == "한국어 문단입니다."

    def test_multiple_block_types(self):
        md = "# 제목\n\n문단\n\n- 목록\n\n---"
        blocks = convert(md)
        types = [b["type"] for b in blocks]
        assert "heading_1" in types
        assert "paragraph" in types
        assert "bulleted_list_item" in types
        assert "divider" in types