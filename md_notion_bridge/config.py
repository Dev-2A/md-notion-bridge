from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class Config:
    """md-notion-bridge 전역 설정"""
    
    # Notion API
    api_key: str = field(default_factory=lambda: os.getenv("NOTION_API_KEY", ""))
    default_page_id: str = field(
        default_factory=lambda: os.getenv("NOTION_DEFAULT_PAGE_ID", "")
    )
    
    # 변환 옵션
    notion_version: str = "2022-06-28"
    max_block_depth: int = 3           # Notion 블록 중첩 최대 깊이
    chunk_size: int = 100              # 배치 처리 시 한 번에 업로드할 블록 수
    
    # 한국어 옵션
    normalize_korean: bool = True      # 한국어 유니코드 정규화 여부
    
    def validate(self) -> None:
        """필수 설정값 검증"""
        if not self.api_key:
            raise ValueError(
                "NOTION_API_KEY가 설정되지 않았습니다.\n"
                ".env 파일에 NOTION_API_KEY를 입력해주세요."
            )


# 싱글턴 인스턴스
config = Config()