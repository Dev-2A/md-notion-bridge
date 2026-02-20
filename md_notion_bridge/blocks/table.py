from __future__ import annotations


def build_table_blocks(rows: list[list[str]], has_header: bool = True) -> dict:
    """마크다운 표 rows → Notion table 블록"""
    table_rows = []
    for i, row in enumerate(rows):
        cells = []
        for cell in row:
            from ..md_to_notion import parse_inline
            cells.append(parse_inline(cell.strip()))
        table_rows.append({
            "type": "table_row",
            "table_row": {"cells": cells},
        })
    
    return {
        "type": "table",
        "table": {
            "table_width": len(rows[0]) if rows else 0,
            "has_column_header": has_header,
            "has_row_header": False,
            "children": table_rows,
        },
    }


def parse_table_block(block: dict, children: list[dict]) -> str:
    """Notion table 블록 → 마크다운 표"""
    has_header = block["table"].get("has_column_header", False)
    rows = []
    
    for row_block in children:
        cells = row_block["table_row"]["cells"]
        row_texts = []
        for cell in cells:
            text = "".join(t["plain_text"] for t in cell)
            row_texts.append(text)
        rows.append("| " + " | ".join(row_texts) + " |")
    
    if not rows:
        return ""
    
    if has_header and len(rows) >= 1:
        col_count = len(children[0]["table_row"]["cells"]) if children else 0
        separator = "| " + " | ".join(["---"] * col_count) + " |"
        rows.insert(1, separator)
    
    return "\n".join(rows)