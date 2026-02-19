from __future__ import annotations


def build_image_block(url: str, caption: str = "") -> dict:
    """이미지 Notion 블록 생성 (외부 URL 방식)"""
    block: dict = {
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": url},
        },
    }
    if caption:
        block["image"]["caption"] = [
            {"type": "text", "text": {"content": caption}}
        ]
    return block


def parse_image_block(block: dict) -> str:
    """Notion 이미지 블록 → 마크다운 이미지"""
    image = block["image"]
    img_type = image.get("type", "external")
    
    if img_type == "external":
        url = image["external"]["url"]
    else:
        # file 타입 (Notion 업로드 이미지) - URL 만료 가능성 있음
        url = image["file"]["url"]
    
    caption_parts = image.get("caption", [])
    caption = "".join(t["plain_text"] for t in caption_parts)
    
    return f"![{caption}]({url})"


def parse_image_block_with_warning(block: dict) -> str:
    """Notion 업로드 이미지의 경우 만료 경고 주석 추가"""
    image = block["image"]
    result = parse_image_block(block)
    
    if image.get("type") == "file":
        result += "\n<!-- ⚠️ Notion 업로드 이미지는 URL이 만료될 수 있습니다 -->"
    
    return result