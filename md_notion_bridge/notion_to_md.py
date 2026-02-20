from __future__ import annotations

from .blocks import parse_code_block, parse_image_block_with_warning, parse_table_block
from .utils.korean import normalize


# ------------------------------------------------------------------ #
# rich_text → 마크다운 인라인 변환
# ------------------------------------------------------------------ #

def rich_text_to_md(rich_texts: list[dict]) -> str:
    """Notion rich_text 리스트 → 마크다운 인라인 문자열"""
    result = []
    for rt in rich_texts:
        text = normalize(rt.get("plain_text", ""))
        annotations = rt.get("annotations", {})
        href = rt.get("href")
        
        # 링크 처리 (어노테이션보다 먼저)
        if href:
            text = f"[{text}]({href})"
        else:
            # 어노테이션 적용 (순서 중요)
            if annotations.get("code"):
                text = f"`{text}`"
            if annotations.get("bold"):
                text = f"**{text}**"
            if annotations.get("italic"):
                text = f"*{text}*"
            if annotations.get("strikethrough"):
                text = f"~~{text}~~"
            if annotations.get("underline"):
                # 마크다운 표준 밑줄 없음 → HTML 태그로 대체
                text = f"<u>{text}</u>"
        
        result.append(text)
    
    return "".join(result)


# ------------------------------------------------------------------ #
# 블록 타입별 변환
# ------------------------------------------------------------------ #

def _convert_block(block: dict, depth: int = 0) -> str:
    """단일 Notion 블록 → 마크다운 문자열"""
    block_type = block.get("type", "")
    data = block.get(block_type, {})
    children = block.get("children", [])
    indent = " " * depth    # 중첩 목록용 들여쓰기
    
    # ── 제목 ──────────────────────────────────────────────────────
    if block_type == "heading_1":
        return f"# {rich_text_to_md(data.get('rich_text', []))}"
    if block_type == "heading_2":
        return f"## {rich_text_to_md(data.get('rich_text', []))}"
    if block_type == "heading_3":
        return f"### {rich_text_to_md(data.get('rich_text', []))}"
    
    # ── 문단 ──────────────────────────────────────────────────────
    if block_type == "paragraph":
        text = rich_text_to_md(data.get("rich_text", []))
        if not text.strip():
            return ""
        return text
    
    # ── 목록 ──────────────────────────────────────────────────────
    if block_type == "bulleted_list_item":
        text = rich_text_to_md(data.get("rich_text", []))
        result = f"{indent}- {text}"
        if children:
            child_lines = _convert_blocks(children, depth + 1)
            result += "\n" + child_lines
        return result
    
    if block_type == "numbered_list_item":
        text = rich_text_to_md(data.get("rich_text", []))
        result = f"{indent}1. {text}"
        if children:
            child_lines = _convert_blocks(children, depth + 1)
            result += "\n" + child_lines
        return result
    
    # ── 인용문 ────────────────────────────────────────────────────
    if block_type == "quote":
        text = rich_text_to_md(data.get("rich_text", []))
        return f"> {text}"
    
    # ── 콜아웃 (Notion 전용 → 인용문으로 변환) ───────────────────
    if block_type == "callout":
        text = rich_text_to_md(data.get("rich_text", []))
        icon = data.get("icon", {})
        emoji = icon.get("emoji", "💡") if icon.get("type") == "emoji" else "💡"
        return f"> {emoji} {text}"
    
    # ── 토글 (Notion 전용 → 일반 문단 + 자식 블록) ───────────────
    if block_type == "toggle":
        text = rich_text_to_md(data.get("rich_text", []))
        result = f"**{text}**"
        if children:
            child_lines = _convert_blocks(children, depth)
            result += "\n" + child_lines
        return result
    
    # ── 코드블록 ──────────────────────────────────────────────────
    if block_type == "code":
        return parse_code_block(block)
    
    # ── 이미지 ────────────────────────────────────────────────────
    if block_type == "image":
        return parse_image_block_with_warning(block)
    
    # ── 표 ────────────────────────────────────────────────────────
    if block_type == "table":
        return parse_table_block(block, children)
    
    if block_type == "table_row":
        # table 블록 안에서 처리되므로 단독 호출 시 스킵
        return ""
    
    # ── 수평선 ────────────────────────────────────────────────────
    if block_type == "divider":
        return "---"
    
    # ── 할일 목록 ─────────────────────────────────────────────────
    if block_type == "to_do":
        text = rich_text_to_md(data.get("rich_text", []))
        checked = "x" if data.get("checked") else " "
        return f"{indent}- [{checked}] {text}"
    
    # ── 수식 ──────────────────────────────────────────────────────
    if block_type == "equation":
        expr = data.get("expression", "")
        return f"$$\n{expr}\n$$"
    
    # ── 지원하지 않는 블록 타입 ───────────────────────────────────
    return f"<!-- unsupported block: {block_type} -->"


def _convert_blocks(blocks: list[dict], depth: int = 0) -> str:
    """블록 리스트 → 마크다운 문자열 (빈 줄 처리 포함)"""
    lines: list[str] = []
    prev_type = ""
    
    for block in blocks:
        block_type = block.get("type", "")
        
        # 표 블록은 자식(table_row)을 직접 받아서 처리
        if block_type == "table_row":
            continue
        
        converted = _convert_block(block, depth)
        if converted == "":
            if prev_type not in ("", "paragraph"):
                lines.append("")
            prev_type = ""
            continue
        
        # 목록 연속 시 빈 줄 삽입 안 함, 그 외엔 블록 사이 빈 줄 추가
        needs_blank = (
            prev_type != ""
            and not (
                block_type in ("bulleted_list_item", "numbered_list_item", "to_do")
                and prev_type in ("bulleted_list_item", "numbered_list_item", "to_do")
            )
        )
        if needs_blank:
            lines.append("")
        
        # 구분선은 앞뒤 빈 줄 강제
        if block_type == "divider":
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(converted)
            lines.append("")
        else:
            lines.append(converted)
        
        prev_type = block_type
    
    # 맨 끝 빈 줄 제거
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


# ------------------------------------------------------------------ #
# 공개 인터페이스
# ------------------------------------------------------------------ #

def convert(blocks: list[dict]) -> str:
    """Notion 블록 리스트 → 마크다운 문자열"""
    return _convert_blocks(blocks)

def convert_page(page: dict, blocks: list[dict]) -> str:
    """Notion 페이지 메타 + 블록 → 마크다운 문자열
    
    페이지 제목을 H1으로 삽입한 뒤 본문 블록을 변환합니다.
    """
    try:
        title_prop = page["properties"]["title"]["title"]
        title = "".join(normalize(t["plain_text"]) for t in title_prop)
    except (KeyError, IndexError):
        title = "Untitled"
    
    body = convert(blocks)
    return f"# {title}\n\n{body}" if body else f"# {title}"

def convert_to_file(blocks: list[dict], path: str) -> None:
    """변환 결과를 파일로 저장"""
    content = convert(blocks)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)