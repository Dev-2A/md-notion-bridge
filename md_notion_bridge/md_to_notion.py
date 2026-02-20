from __future__ import annotations

import re

from .blocks import build_code_block, build_image_block, build_table_blocks
from .utils.korean import normalize, normalize_markdown_korean, rich_text_with_limit


# ------------------------------------------------------------------ #
# 인라인 rich_text 변환
# ------------------------------------------------------------------ #

def parse_inline(text: str) -> list[dict]:
    """인라인 마크다운 → Notion rich_text 리스트
    
    지원: **굵게**, *기울임*, ~~취소선~~, `인라인 코드`, [링크](url)
    """
    result: list[dict] = []
    # 패턴 순서 중요 (긴 패턴 먼저)
    pattern = re.compile(
        r"(\*\*(.+?)\*\*)"              # **굵게**
        r"|(\*(.+?)\*)"                 # *기울임*
        r"|(~~(.+?)~~)"                 # ~~취소선~~
        r"|(`(.+?)`)"                   # `코드`
        r"|(\[(.+?)\]\((.+?)\))"        # [텍스트](url)
    )
    
    last = 0
    for m in pattern.finditer(text):
        # 매칭 이전 일반 텍스트
        if m.start() > last:
            result.append(_plain(text[last:m.start()]))
        
        if m.group(1):      # **굵게**
            result.append(_annotated(m.group(2), bold=True))
        elif m.group(3):    # *기울임*
            result.append(_annotated(m.group(4), italic=True))
        elif m.group(5):    # ~~취소선~~
            result.append(_annotated(m.group(6), strikethrough=True))
        elif m.group(7):    # `코드`
            result.append(_annotated(m.group(8), code=True))
        elif m.group(9):    # [링크](url)
            result.append(_link(m.group(10), m.group(11)))
        
        last = m.end()
    
    # 나머지 텍스트
    if last < len(text):
        result.append(_plain(text[last:]))
    
    return result if result else [_plain("")]


def _plain(text: str) -> dict:
    # 2000자 초과 시 자동 분할 (첫 번째 청크만 반환, 나머지는 parse_inline에서 처리)
    chunks = rich_text_with_limit(text)
    return chunks[0] if chunks else {"type": "text", "text": {"content": ""}}


def _plain_all(text: str) -> list[dict]:
    """2000자 초과 텍스트를 분할한 rich_text 리스트 전체 반환"""
    return rich_text_with_limit(text)


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
    tag = f"heading_{level}"
    return {
        "type": tag,
        tag: {"rich_text": parse_inline(text)},
    }


def _paragraph(text: str) -> dict:
    return {
        "type": "paragraph",
        "paragraph": {"rich_text": parse_inline(text)},
    }


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
    return {
        "type": "quote",
        "quote": {"rich_text": parse_inline(text)},
    }


def _divider() -> dict:
    return {"type": "divider", "divider": {}}


# ------------------------------------------------------------------ #
# 표 파싱 헬퍼
# ------------------------------------------------------------------ #

def _is_separator_row(line: str) -> bool:
    """| --- | --- | 형태의 구분선 여부"""
    return bool(re.match(r"^\|[\s\-:|]+\|$", line.strip()))


def _parse_table_row(line: str) -> list[str]:
    """| a | b | c | → ['a', 'b', 'c']"""
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
        
        # ── 코드블록 (``` 로 시작) ──────────────────────────────────
        if line.startswith("```"):
            lang = line[3:].strip()
            code_liens: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_liens.append(lines[i])
                i += 1
            blocks.append(build_code_block("\n".join(code_liens), lang))
            i += 1
            continue
        
        # ── 표 ────────────────────────────────────────────────────
        if line.startswith("|") and "|" in line[1:]:
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            
            # 구분선 제거하고 rows 추출
            rows = [
                _parse_table_row(l)
                for l in table_lines
                if not _is_separator_row(l)
            ]
            if rows:
                has_header = any(_is_separator_row(l) for l in table_lines)
                blocks.append(build_table_blocks(rows, has_header))
            continue
        
        # ── 제목 ──────────────────────────────────────────────────
        heading_match = re.match(r"^(#{1,3})\s+(.*)", line)
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
        
        # ── 순서 없는 목록 ────────────────────────────────────────
        ul_match = re.match(r"^[-*+]\s+(.*)", line)
        if ul_match:
            blocks.append(_bulleted(ul_match.group(1)))
            i += 1
            continue
        
        # ── 순서 있는 목록 ────────────────────────────────────────
        ol_match = re.match(r"^\d+\.\s+(.*)", line)
        if ol_match:
            blocks.append(_numbered(ol_match.group(1)))
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
        
        # ── 일반 문단 ─────────────────────────────────────────────
        blocks.append(_paragraph(line))
        i += 1
    
    return blocks


def convert_file(path: str) -> list[dict]:
    """마크다운 파일 → Notion 블록 리스트"""
    with open(path, encoding="utf-8") as f:
        return convert(f.read())