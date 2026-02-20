from __future__ import annotations


class MdNotionBridgeError(Exception):
    """md-notion-bridge 기본 예외"""


class NotionAPIError(MdNotionBridgeError):
    """Notion API 호출 실패"""
    
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ConversionError(MdNotionBridgeError):
    """블록 변환 실패"""
    
    def __init__(self, message: str, source: str = "") -> None:
        super().__init__(message)
        self.source = source    # 실패한 파일 경로 또는 블록 ID


class ConfigError(MdNotionBridgeError):
    """설정 오류"""


class FileSizeError(MdNotionBridgeError):
    """파일 크기 초과"""