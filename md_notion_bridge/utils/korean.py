from __future__ import annotations

import re
import unicodedata


def normalize(text: str) -> str:
    """한국어 유니코드 NFC 정규화
    
    macOS에서 작성된 파일은 NFD(자모 분리) 형태로 저장되어
    Windows/Linux에서 깨져 보일 수 있습니다. NFC로 통일합니다.
    """
    return unicodedata.normalize("NFC", text)


def is_korean(text: str) -> bool:
    """한글 포함 여부 확인"""
    return any("\uAC00" <= ch <= "\uD7A3" for ch in text)


def has_korean(text: str) -> bool:
    """한글 자모 또는 완성형 포함 여부 (자모 단독도 감지)"""
    return any(
        "\u1100" <= ch <= "\u11FF"  # 한글 자모
        or "\uAC00" <= ch <= "\uD7A3"   # 한글 완성형
        or "\u3130" <= ch <= "\u318F"   # 호환 자모
        for ch in text
    )


# ------------------------------------------------------------------ #
# 페이지 제목 정제
# ------------------------------------------------------------------ #

def sanitize_page_title(title: str) -> str:
    """Notion 페이지 제목으로 사용 불가한 문자 제거"""
    title = title.replace("\n", " ").replace("\r", "")
    title = title.strip()
    return title if title else "Untitled"


# ------------------------------------------------------------------ #
# 마크다운 한국어 엣지케이스 처리
# ------------------------------------------------------------------ #

def fix_korean_bold(text: str) -> str:
    """한국어 굵게(**) 파싱 오류 보정
    
    일부 마크다운 파서는 **한국어** 처리 시
    단어 경계를 잘못 인식합니다. 앞뒤 공백을 추가해 보정합니다.
    """
    # **텍스트** 패턴에서 한국어가 포함된 경우 앞뒤 공백 보장
    def replacer(m: re.Match) -> str:
        inner = m.group(1)
        if has_korean(inner):
            return f" **{inner}** "
        return m.group(0)
    
    return re.sub(r"\*\*(.+?)\*\*", replacer, text).strip()


def fix_korean_italic(text: str) -> str:
    """한국어 기울임(*) 파싱 오류 보정"""
    def replacer(m: re.Match) -> str:
        inner = m.group(1)
        if has_korean(inner):
            return f" *{inner}* "
        return m.group(0)
    
    # **굵게** 이미 처리된 부분 제외하고 단일 * 처리
    return re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", replacer, text).strip()


def normalize_punctuation(text: str) -> str:
    """한국어 문서에서 자주 혼용되는 문장부호 정규화
    
    - 전각 문자(！, ？, ：) → 반각
    - 중국어 따옴표(「」『』) → 유지 (한국어 출판 관례 존중)
    - 연속 공백 → 단일 공백
    """
    replacements = {
        "！": "!",
        "？": "?",
        "：": ":",
        "；": ";",
        "，": ",",
        "．": ".",
        "\u3000": " ",   # 전각 공백 → 반각
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    
    # 연속 공백 정리 (줄바꿈 제외)
    text = re.sub(r"[^\S\n]+", " ", text)
    return text


def normalize_markdown_korean(text: str) -> str:
    """마크다운 문자열 전체에 한국어 최적화 적용"""
    text = normalize(text)          # NFC 정규화
    text = normalize_punctuation(text)  # 문장부호 정규화
    return text


# ------------------------------------------------------------------ #
# Notion rich_text 길이 제한 처리
# ------------------------------------------------------------------ #

NOTION_TEXT_LIMIT = 2000    # Notion rich_text 단일 객체 최대 글자 수


def split_long_text(text: str, limit: int = NOTION_TEXT_LIMIT) -> list[str]:
    """Notion API 제한(2000자)을 초과하는 텍스트를 청크로 분할
    
    한국어는 문장 단위(。, .)로 자르고,
    그래도 초과하면 강제로 limit 단위로 자릅니다.
    """
    if len(text) <= limit:
        return [text]
    
    chunks: list[str] = []
    # 문장 단위로 먼저 분할 시도
    sentences = re.split(r"(?<=[.。!?])\s+", text)
    current = ""
    
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= limit:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            # 문장 자체가 limit 초과 → 강제 분할
            while len(sentence) > limit:
                chunks.append(sentence[:limit])
                sentence = sentence[limit:]
            current = sentence
    
    if current:
        chunks.append(current)
    
    return chunks


def rich_text_with_limit(text: str, annotations: dict | None = None) -> list[dict]:
    """2000자 제한을 고려한 rich_text 객체 리스트 생성"""
    chunks = split_long_text(normalize(text))
    result = []
    for chunk in chunks:
        obj: dict = {"type": "text", "text": {"content": chunk}}
        if annotations:
            obj["annotations"] = annotations
        result.append(obj)
    return result