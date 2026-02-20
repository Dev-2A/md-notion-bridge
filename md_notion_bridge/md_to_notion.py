from __future__ import annotations

import re

from .blocks import build_code_block, build_image_block, build_table_blocks
from .utils.korean import normalize, normalize_markdown_korean, rich_text_with_limit


# ------------------------------------------------------------------ #
# 인라인 rich_text 변환
# ------------------------------------------------------------------ #

def parse_inline(text: str) -> list[dict]:
    result: list[dict] = []
    pattern = re.compile(
        r"(\*\*(.+?)\*\*)"
        r"|(\*(.+?)\*)"
        r"|(~~(.+?)~~)"
        r"|(`(.+?)`)"
        r"|(\[(.+?)\]\((.+?)\))"
    )
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            result.extend(rich_text_with_limit(text[last:m.start()]))
        if m.group(1):
            result.append(_annotated(m.group(2), bold=True))
        elif m.group(3):
            result.append(_annotated(m.group(4), italic=True))
        elif m.group(5):
            result.append(_annotated(m.group(6), strikethrough=True))
        elif m.group(7):
            result.append(_annotated(m.group(8), code=True))
        elif m.group(9):
            result.append(_link(m.group(10), m.group(11)))
        last = m.end()
    if last < len(text):
        result.extend(rich_text_with_limit(text[last:]))
    return result if result else [_plain("")]


def _plain(text: str) -> dict:
    return {"type": "text", "text": {"content": normalize(text)}}


def _annotated(text: str, **kwargs) -> dict:
    return {
        "type": "text",
        "text": {"content": normalize(text)},
        "annotations": kwargs,
    }


def _link(text: str, url: str) -> dict:
    return {
        "type": "text",
        "text": {"content": normalize(text), "link": {"url": url}},
    }


# ------------------------------------------------------------------ #
# 블록 빌더 헬퍼
# ------------------------------------------------------------------ #

def _heading(level: int, text: str) -> dict:
    clamped = min(level, 3)
    tag = f"heading_{clamped}"
    return {"type": tag, tag: {"rich_text": parse_inline(text)}}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "paragraph": {"rich_text": parse_inline(text)}}


def _bulleted(text: str) -> dict:
    return {
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": parse_inline(text)},
    }


def _numbered(text: str) -> dict:
    return {
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": parse_inline(text)},
    }


def _quote(text: str) -> dict:
    return {"type": "quote", "quote": {"rich_text": parse_inline(text)}}


def _divider() -> dict:
    return {"type": "divider", "divider": {}}


# ------------------------------------------------------------------ #
# 표 파싱 헬퍼
# ------------------------------------------------------------------ #

def _is_separator_row(line: str) -> bool:
    return bool(re.match(r"^\|[\s\-:|]+\|$", line.strip()))


def _parse_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


# ------------------------------------------------------------------ #
# 메인 변환 함수
# ------------------------------------------------------------------ #

def convert(markdown: str, korean_optimize: bool = True) -> list[dict]:
    """마크다운 문자열 → Notion 블록 리스트"""
    if korean_optimize:
        markdown = normalize_markdown_korean(markdown)

    blocks: list[dict] = []
    lines = markdown.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── 코드블록 ──────────────────────────────────────────────
        if line.startswith("```"):
            lang = line[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append(build_code_block("\n".join(code_lines), lang))
            i += 1
            continue

        # ── 표 ────────────────────────────────────────────────────
        if line.startswith("|") and "|" in line[1:]:
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = [
                _parse_table_row(l)
                for l in table_lines
                if not _is_separator_row(l)
            ]
            if rows:
                has_header = any(_is_separator_row(l) for l in table_lines)
                blocks.append(build_table_blocks(rows, has_header))
            continue

        # ── 제목 (H1~H6) ──────────────────────────────────────────
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            level = len(heading_match.group(1))
            blocks.append(_heading(level, heading_match.group(2)))
            i += 1
            continue

        # ── 수평선 ────────────────────────────────────────────────
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", line.strip()):
            blocks.append(_divider())
            i += 1
            continue

        # ── 인용문 ────────────────────────────────────────────────
        if line.startswith("> "):
            blocks.append(_quote(line[2:]))
            i += 1
            continue

        # ── 순서 없는 목록 (중첩 지원) ────────────────────────────
        ul_match = re.match(r"^( *)[-*+] (.*)", line)
        if ul_match:
            spaces = ul_match.group(1)
            text = ul_match.group(2)
            # 할일 목록 체크
            todo_match = re.match(r"^\[(x| )\] (.*)", text, re.IGNORECASE)
            if todo_match:
                checked = todo_match.group(1).lower() == "x"
                todo_block = {
                    "type": "to_do",
                    "to_do": {
                        "rich_text": parse_inline(todo_match.group(2)),
                        "checked": checked,
                    },
                }
                blocks.append(todo_block)
            else:
                block = _bulleted(text)
                if len(spaces) >= 2 and blocks and blocks[-1]["type"] == "bulleted_list_item":
                    inner = blocks[-1]["bulleted_list_item"]
                    inner.setdefault("children", [])
                    inner["children"].append(block)
                else:
                    blocks.append(block)
            i += 1
            continue

        # ── 순서 있는 목록 (중첩 지원) ────────────────────────────
        ol_match = re.match(r"^( *)\d+\. (.*)", line)
        if ol_match:
            spaces = ol_match.group(1)
            text = ol_match.group(2)
            block = _numbered(text)
            if len(spaces) >= 2 and blocks and blocks[-1]["type"] == "numbered_list_item":
                inner = blocks[-1]["numbered_list_item"]
                inner.setdefault("children", [])
                inner["children"].append(block)
            else:
                blocks.append(block)
            i += 1
            continue

        # ── 이미지 ────────────────────────────────────────────────
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line)
        if img_match:
            caption, url = img_match.group(1), img_match.group(2)
            blocks.append(build_image_block(url, caption))
            i += 1
            continue

        # ── 빈 줄 ─────────────────────────────────────────────────
        if line.strip() == "":
            i += 1
            continue

        # ── 일반 문단 (연속 줄 병합) ──────────────────────────────
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            if (
                not next_line.strip()
                or next_line.startswith("#")
                or next_line.startswith(">")
                or next_line.startswith("```")
                or next_line.startswith("|")
                or re.match(r"^\s*[-*+] ", next_line)
                or re.match(r"^\s*\d+\. ", next_line)
                or re.match(r"^(-{3,}|\*{3,}|_{3,})$", next_line.strip())
            ):
                break
            para_lines.append(next_line)
            i += 1
        blocks.append(_paragraph(" ".join(para_lines)))

    return blocks


def convert_file(path: str, korean_optimize: bool = True) -> list[dict]:
    """마크다운 파일 → Notion 블록 리스트"""
    with open(path, encoding="utf-8") as f:
        return convert(f.read(), korean_optimize=korean_optimize)