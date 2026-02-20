from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from notion_client.errors import APIResponseError

from .client import NotionClient
from .exceptions import ConversionError, FileSizeError
from .md_to_notion import convert_file
from .notion_to_md import convert_page

# Notion API 속도 제한 대응 (초당 3회 제한)
REQUEST_INTERVAL = 0.4   # 초
MAX_FILE_SIZE_MB = 5
MAX_RETRIES = 3


# ------------------------------------------------------------------ #
# 결과 데이터클래스
# ------------------------------------------------------------------ #

@dataclass
class PushResult:
    """단일 파일 push 결과"""
    file: str
    success: bool
    page_url: str = ""
    block_count: int = 0
    error: str = ""


@dataclass
class PullResult:
    """단일 페이지 pull 결과"""
    page_id: str
    success: bool
    output_path: str = ""
    block_count: int = 0
    error: str = ""


@dataclass
class BatchReport:
    """배치 처리 전체 결과 리포트"""
    total: int = 0
    success: int = 0
    failed: int = 0
    results: list[PushResult | PullResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return (self.success / self.total * 100) if self.total else 0.0

    def summary(self) -> str:
        return (
            f"총 {self.total}건 | "
            f"성공 {self.success}건 | "
            f"실패 {self.failed}건 | "
            f"성공률 {self.success_rate:.1f}%"
        )


# ------------------------------------------------------------------ #
# 유틸
# ------------------------------------------------------------------ #

def _check_file_size(path: Path) -> None:
    """파일 크기 제한 검사"""
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise FileSizeError(
            f"파일 크기 초과: {size_mb:.1f}MB (최대 {MAX_FILE_SIZE_MB}MB)"
        )


def _retry(func, retries: int = MAX_RETRIES, delay: float = 1.0):
    """API 호출 재시도 래퍼 (지수 백오프)"""
    for attempt in range(retries):
        try:
            return func()
        except APIResponseError as e:
            # 429 Rate Limit → 대기 후 재시도
            if e.status == 429 and attempt < retries - 1:
                wait = delay * (2 ** attempt)
                time.sleep(wait)
                continue
            # 그 외 에러는 즉시 raise
            raise
    return None


# ------------------------------------------------------------------ #
# 배치 Push (md → Notion)
# ------------------------------------------------------------------ #

def batch_push(
    files: list[Path],
    client: NotionClient,
    parent_id: str,
    korean_optimize: bool = True,
    on_progress=None,  # 콜백: (current, total, result) → None
) -> BatchReport:
    """마크다운 파일 목록을 Notion에 일괄 업로드"""
    report = BatchReport(total=len(files))

    for idx, file in enumerate(files):
        result = PushResult(file=file.name, success=False)

        try:
            # 파일 크기 검사
            _check_file_size(file)

            # 마크다운 → 블록 변환
            blocks = convert_file(str(file), korean_optimize=korean_optimize)
            if not blocks:
                raise ConversionError("변환된 블록이 없습니다.", source=str(file))

            # 제목 추출
            title = file.stem
            content = file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            # Notion 업로드 (재시도 포함)
            page = _retry(
                lambda: client.create_page(parent_id, title, children=blocks[:100])
            )
            page_id = page["id"]

            # 100블록 초과분 추가
            if len(blocks) > 100:
                for i in range(100, len(blocks), 100):
                    chunk = blocks[i:i + 100]
                    _retry(lambda: client.append_blocks(page_id, chunk))
                    time.sleep(REQUEST_INTERVAL)

            result.success = True
            result.page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
            result.block_count = len(blocks)
            report.success += 1

        except FileSizeError as e:
            result.error = f"[크기 초과] {e}"
            report.failed += 1
        except ConversionError as e:
            result.error = f"[변환 실패] {e}"
            report.failed += 1
        except APIResponseError as e:
            result.error = f"[API 오류 {e.status}] {e}"
            report.failed += 1
        except Exception as e:
            result.error = f"[알 수 없는 오류] {e}"
            report.failed += 1

        report.results.append(result)

        if on_progress:
            on_progress(idx + 1, len(files), result)

        # API 속도 제한 대응
        time.sleep(REQUEST_INTERVAL)

    return report


# ------------------------------------------------------------------ #
# 배치 Pull (Notion → md)
# ------------------------------------------------------------------ #

def batch_pull(
    page_ids: list[str],
    client: NotionClient,
    output_dir: Path,
    on_progress=None,
) -> BatchReport:
    """Notion 페이지 목록을 마크다운 파일로 일괄 추출"""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = BatchReport(total=len(page_ids))

    for idx, raw_id in enumerate(page_ids):
        clean_id = NotionClient.extract_page_id(raw_id)
        result = PullResult(page_id=clean_id, success=False)

        try:
            page = _retry(lambda: client.get_page(clean_id))
            blocks = client.get_block_children(clean_id)
            markdown = convert_page(page, blocks)

            # 파일명 결정
            title = client.get_page_title(page)
            safe_title = "".join(
                c for c in title if c not in r'\/:*?"<>|'
            ).strip() or clean_id
            output_path = output_dir / f"{safe_title}.md"

            # 파일명 중복 처리
            counter = 1
            while output_path.exists():
                output_path = output_dir / f"{safe_title}_{counter}.md"
                counter += 1

            output_path.write_text(markdown, encoding="utf-8")

            result.success = True
            result.output_path = str(output_path)
            result.block_count = len(blocks)
            report.success += 1

        except APIResponseError as e:
            result.error = f"[API 오류 {e.status}] {e}"
            report.failed += 1
        except Exception as e:
            result.error = f"[알 수 없는 오류] {e}"
            report.failed += 1

        report.results.append(result)

        if on_progress:
            on_progress(idx + 1, len(page_ids), result)

        time.sleep(REQUEST_INTERVAL)

    return report