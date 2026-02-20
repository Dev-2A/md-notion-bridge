"""Notion → 마크다운 변환기 테스트"""
from __future__ import annotations

import pytest
from md_notion_bridge.notion_to_md import convert, rich_text_to_md


# ------------------------------------------------------------------ #
# rich_text_to_md 테스트
# ------------------------------------------------------------------ #

def _rt(text: str, **annotations) -> dict:
    """테스트용 rich_text 객체 생성 헬퍼"""
    return {
        "plain_text": text,
        "annotations": {
            "bold": False,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            **annotations,
        },
        "href": None,
    }


class TestRichTextToMd:

    def test_plain(self):
        assert rich_text_to_md([_rt("안녕하세요")]) == "안녕하세요"

    def test_bold(self):
        assert rich_text_to_md([_rt("굵게", bold=True)]) == "**굵게**"

    def test_italic(self):
        assert rich_text_to_md([_rt("기울임", italic=True)]) == "*기울임*"

    def test_strikethrough(self):
        assert rich_text_to_md([_rt("취소선", strikethrough=True)]) == "~~취소선~~"

    def test_code(self):
        assert rich_text_to_md([_rt("코드", code=True)]) == "`코드`"

    def test_underline(self):
        assert rich_text_to_md([_rt("밑줄", underline=True)]) == "<u>밑줄</u>"

    def test_link(self):
        rt = {
            "plain_text": "링크",
            "annotations": {"bold": False, "italic": False,
                            "strikethrough": False, "underline": False, "code": False},
            "href": "https://example.com",
        }
        assert rich_text_to_md([rt]) == "[링크](https://example.com)"

    def test_multiple(self):
        result = rich_text_to_md([_rt("앞 "), _rt("굵게", bold=True), _rt(" 뒤")])
        assert result == "앞 **굵게** 뒤"


# ------------------------------------------------------------------ #
# convert 테스트
# ------------------------------------------------------------------ #

def _block(block_type: str, rich_text: list[dict] | None = None, **extra) -> dict:
    """테스트용 Notion 블록 생성 헬퍼"""
    data = {}
    if rich_text is not None:
        data["rich_text"] = rich_text
    data.update(extra)
    return {"type": block_type, block_type: data, "children": []}


class TestConvert:

    def test_heading1(self):
        block = _block("heading_1", rich_text=[_rt("제목")])
        assert convert([block]) == "# 제목"

    def test_heading2(self):
        block = _block("heading_2", rich_text=[_rt("소제목")])
        assert convert([block]) == "## 소제목"

    def test_heading3(self):
        block = _block("heading_3", rich_text=[_rt("소소제목")])
        assert convert([block]) == "### 소소제목"

    def test_paragraph(self):
        block = _block("paragraph", rich_text=[_rt("문단")])
        assert convert([block]) == "문단"

    def test_empty_paragraph(self):
        block = _block("paragraph", rich_text=[_rt("")])
        assert convert([block]) == ""

    def test_bulleted_list(self):
        blocks = [
            _block("bulleted_list_item", rich_text=[_rt("항목 하나")]),
            _block("bulleted_list_item", rich_text=[_rt("항목 둘")]),
        ]
        result = convert(blocks)
        assert "- 항목 하나" in result
        assert "- 항목 둘" in result

    def test_numbered_list(self):
        blocks = [
            _block("numbered_list_item", rich_text=[_rt("첫 번째")]),
            _block("numbered_list_item", rich_text=[_rt("두 번째")]),
        ]
        result = convert(blocks)
        assert "1. 첫 번째" in result
        assert "1. 두 번째" in result

    def test_quote(self):
        block = _block("quote", rich_text=[_rt("인용문")])
        assert convert([block]) == "> 인용문"

    def test_divider(self):
        block = _block("divider")
        assert convert([block]) == "---"

    def test_to_do_checked(self):
        block = _block("to_do", rich_text=[_rt("완료")], checked=True)
        assert convert([block]) == "- [x] 완료"

    def test_to_do_unchecked(self):
        block = _block("to_do", rich_text=[_rt("미완료")], checked=False)
        assert convert([block]) == "- [ ] 미완료"

    def test_code_block(self):
        block = _block("code", rich_text=[_rt("print('hi')")], language="python")
        result = convert([block])
        assert "```python" in result
        assert "print('hi')" in result

    def test_unsupported_block(self):
        block = _block("embed")
        result = convert([block])
        assert "unsupported block" in result

    def test_empty_blocks(self):
        assert convert([]) == ""

    def test_blank_between_different_types(self):
        """서로 다른 블록 타입 사이에 빈 줄 삽입"""
        blocks = [
            _block("heading_1", rich_text=[_rt("제목")]),
            _block("paragraph", rich_text=[_rt("문단")]),
        ]
        result = convert(blocks)
        assert "\n\n" in result

    def test_no_blank_between_same_list_type(self):
        """같은 목록 타입 사이에는 빈 줄 없음"""
        blocks = [
            _block("bulleted_list_item", rich_text=[_rt("하나")]),
            _block("bulleted_list_item", rich_text=[_rt("둘")]),
        ]
        result = convert(blocks)
        assert "\n\n" not in result