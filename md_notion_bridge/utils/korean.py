from __future__ import annotations

import unicodedata


def normalize(text: str) -> str:
    """한국어 유니코드 정규화 (NFC)
    
    macOS에서 작성된 한국어 파일명/텍스트는 NFD로 분리되어 있어
    Windows/Linux에서 깨져 보일 수 있습니다. NFC로 통일합니다.
    """
    return unicodedata.normalize("NFC", text)


def is_korean(text: str) -> bool:
    """한글 포함 여부 확인"""
    return any("\uAC00" <= ch <= "\uD7A3" for ch in text)


def sanitize_page_title(title: str) -> str:
    """Notion 페이지 제목으로 사용할 수 없는 문자 제거"""
    # Notion 제목에서 줄바꿈 제거
    title = title.replace("\n", " ").replace("\r", "")
    # 앞뒤 공백 제거
    title = title.strip()
    # 빈 제목 대체
    return title if title else "Untitled"