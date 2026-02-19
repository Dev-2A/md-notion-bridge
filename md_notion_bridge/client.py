from __future__ import annotations

from notion_client import Client
from notion_client.errors import APIResponseError

from .config import config


class NotionClient:
    """Notion API 클라이언트 래퍼"""
    
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or config.api_key
        if not key:
            raise ValueError("NOTION_API_KEY가 없습니다.")
        self._client = Client(auth=key)
    
    # ------------------------------------------------------------------ #
    # 페이지 조회
    # ------------------------------------------------------------------ #
    
    def get_page(self, page_id: str) -> dict:
        """페이지 메타데이터 조회"""
        return self._client.pages.retrieve(page_id=page_id)
    
    def get_blocks(self, block_id: str) -> list[dict]:
        """블록 목록 전체 조회 (페이지네이션 자동 처리)"""
        blocks: list[dict] = []
        cursor = None
        
        while True:
            kwargs: dict = {"block_id": block_id, "page_size": 100}
            if cursor:
                kwargs["start_cursor"] = cursor
            
            response = self._client.blocks.children.list(**kwargs)
            blocks.extend(response.get("results", []))
            
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
        
        return blocks
    
    def get_block_children(self, block_id: str) -> list[dict]:
        """자식 블록 재귀 조회"""
        blocks = self.get_blocks(block_id)
        for block in blocks:
            if block.get("has_children"):
                block["children"] = self.get_block_children(block["id"])
            else:
                block["children"] = []
        return blocks
    
    # ------------------------------------------------------------------ #
    # 페이지 생성 / 수정
    # ------------------------------------------------------------------ #
    
    def create_page(
        self,
        parent_id: str,
        title: str,
        children: list[dict] | None = None,
    ) -> dict:
        """새 페이지 생성"""
        payload: dict = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            },
        }
        if children:
            payload["children"] = children[:100]    # 최초 100블록만 가능
        
        return self._client.pages.create(**payload)
    
    def append_blocks(self, block_id: str, children: list[dict]) -> None:
        """블록을 청크 단위로 나눠서 추가"""
        for i in range(0, len(children, config.chunk_size)):
            chunk = children[i : i + config.chunk_size]
            self._client.blocks.children.append(
                block_id=block_id, children=chunk
            )
    
    # ------------------------------------------------------------------ #
    # 유틸
    # ------------------------------------------------------------------ #
    
    def get_page_title(self, page: dict) -> str:
        """페이지 딕셔너리에서 제목 추출"""
        try:
            title_prop = page["properties"]["title"]["title"]
            return "".join(t["plain_text"] for t in title_prop)
        except (KeyError, IndexError):
            return "Untitled"
    
    @staticmethod
    def extract_page_id(url_or_id: str) -> str:
        """Notion URL 또는 ID 문자열에서 순수 page_id 추출"""
        # URL 형식: https://www.notion.so/Title-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        cleaned = url_or_id.strip().split("?")[0].split("#")[0]
        raw_id = cleaned.split("-")[-1].split("/")[-1]
        # 하이픈 없는 32자리 ID → 하이픈 포함 형식으로 변환
        if len(raw_id) == 32 and "-" not in raw_id:
            return (
                f"{raw_id[:8]}-{raw_id[8:12]}-"
                f"{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
            )
        return raw_id