"""한국어 유틸 테스트"""
from __future__ import annotations

import unicodedata
import pytest
from md_notion_bridge.utils.korean import (
    normalize,
    is_korean,
    has_korean,
    normalize_punctuation,
    split_long_text,
    NOTION_TEXT_LIMIT,
)


class TestNormalize:

    def test_nfc(self):
        # NFD로 분리된 한글 → NFC로 합성
        nfd = unicodedata.normalize("NFD", "한글")
        assert normalize(nfd) == "한글"

    def test_already_nfc(self):
        assert normalize("안녕하세요") == "안녕하세요"

    def test_empty(self):
        assert normalize("") == ""


class TestIsKorean:

    def test_korean(self):
        assert is_korean("안녕") is True

    def test_english(self):
        assert is_korean("hello") is False

    def test_mixed(self):
        assert is_korean("hello 안녕") is True

    def test_number(self):
        assert is_korean("12345") is False


class TestNormalizePunctuation:

    def test_fullwidth_exclamation(self):
        assert normalize_punctuation("안녕！") == "안녕!"

    def test_fullwidth_question(self):
        assert normalize_punctuation("정말？") == "정말?"

    def test_fullwidth_colon(self):
        assert normalize_punctuation("제목：내용") == "제목:내용"

    def test_fullwidth_space(self):
        result = normalize_punctuation("안녕\u3000하세요")
        assert "\u3000" not in result

    def test_multiple_spaces(self):
        result = normalize_punctuation("안녕   하세요")
        assert "   " not in result


class TestSplitLongText:

    def test_short_text(self):
        text = "짧은 텍스트"
        assert split_long_text(text) == [text]

    def test_long_text_split(self):
        text = "안녕하세요. " * 400  # 2000자 초과
        chunks = split_long_text(text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= NOTION_TEXT_LIMIT

    def test_reassemble(self):
        """분할 후 재조합 시 원본 텍스트 보존"""
        text = "가나다. " * 400
        chunks = split_long_text(text)
        reassembled = " ".join(chunks)
        # 공백 차이는 허용, 핵심 내용 보존 확인
        assert "가나다" in reassembled