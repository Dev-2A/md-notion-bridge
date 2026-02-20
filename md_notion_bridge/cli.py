from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .client import NotionClient
from .config import config
from .md_to_notion import convert as md_to_blocks, convert_file
from .notion_to_md import convert as blocks_to_md, convert_page, convert_to_file

console = Console()
err_console = Console(stderr=True, style="bold red")


# ------------------------------------------------------------------ #
# 공통 옵션
# ------------------------------------------------------------------ #

def _get_client(api_key: str | None = None) -> NotionClient:
    """클라이언트 생성 (API 키 검증 포함)"""
    try:
        config.validate()
        return NotionClient(api_key)
    except ValueError as e:
        err_console.print(f"❌ {e}")
        sys.exit(1)


# ------------------------------------------------------------------ #
# CLI 그룹
# ------------------------------------------------------------------ #

@click.group()
@click.version_option(package_name="md-notion-bridge")
def main() -> None:
    """🔄 마크다운 ↔ Notion 양방향 변환기"""


# ------------------------------------------------------------------ #
# md → notion
# ------------------------------------------------------------------ #

@main.command("push")
@click.argument("md_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--page-id", "-p",
    default=None,
    help="업로드한 Notion 페이지 ID 또는 URL. 미입력 시 .env의 기본값 사용.",
)
@click.option(
    "--title", "-t",
    default=None,
    help="생성할 Notion 페이지 제목. 미입력 시 마크다운 H1 또는 파일명 사용.",
)
@click.option(
    "--no-korean-opt",
    is_flag=True,
    default=False,
    help="한국어 최적화 비활성화.",
)
def push(md_file: str, page_id: str | None, title: str | None, no_korean_opt: bool) -> None:
    """마크다운 파일을 Notion 페이지로 업로드합니다.
    
    \b
    예시:
        md-notion push README.md
        md-notion push docs/guide.md --page-id https://notion.so/...
        md-notion push report.md --title "월간 리포트"
    """
    client = _get_client()
    parent_id = page_id or config.default_page_id
    
    if not parent_id:
        err_console.print(
            "❌ 페이지 ID가 필요합니다.\n"
            "   --page-id 옵션 또는 .env의 NOTION_DEFAULT_PAGE_ID를 설정해주세요."
        )
        sys.exit(1)
    
    # page_id 정규화
    parent_id = NotionClient.extract_page_id(parent_id)
    
    # 파일명에서 기본 제목 추출
    file_path = Path(md_file)
    if not title:
        # 파일 내 첫 번째 H1 탐색
        content = file_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        title = title or file_path.stem
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("📄 마크다운 파싱 중...", total=None)
        blocks = convert_file(md_file, korean_optimize=not no_korean_opt)
        
        progress.update(task, description="☁️  Notion 페이지 생성 중...")
        page = client.create_page(parent_id, title, children=blocks[:100])
        page_id_created = page["id"]
        
        # 100블록 초과 시 나머지 추가
        if len(blocks) > 100:
            progress.update(task, description="📦 추가 블록 업로드 중...")
            client.append_blocks(page_id_created, blocks[100:])
        
        progress.update(task, description="✅ 완료!")
    
    page_url = f"https://www.notion.so/{page_id_created.replace('-', '')}"
    console.print(
        Panel(
            f"[bold green]✅ 업로드 완료![/bold green]\n\n"
            f"[bold]제목:[/bold] {title}\n"
            f"[bold]블록 수:[/bold] {len(blocks)}\n"
            f"[bold]URL:[/bold] [link={page_url}]{page_url}[/link]",
            title="md-notion push",
            border_style="green",
        )
    )


# ------------------------------------------------------------------ #
# notion → md
# ------------------------------------------------------------------ #

@main.command("pull")
@click.argument("page_id")
@click.option(
    "--output", "-o",
    default=None,
    help="저장할 파일 경로. 미입력 시 페이지 제목.md 로 저장.",
)
@click.option(
    "--stdout",
    is_flag=True,
    default=False,
    help="파일 저장 대신 표준 출력으로 출력.",
)
def pull(page_id: str, output: str | None, stdout: bool) -> None:
    """Notion 페이지를 마크다운 파일로 추출합니다.

    \b
    예시:
        md-notion pull https://notion.so/...
        md-notion pull abc123 --output result.md
        md-notion pull abc123 --stdout
    """
    client = _get_client()
    clean_id = NotionClient.extract_page_id(page_id)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("🔍 페이지 조회 중...", total=None)
        page = client.get_page(clean_id)

        progress.update(task, description="📦 블록 수집 중...")
        blocks = client.get_block_children(clean_id)

        progress.update(task, description="✍️  마크다운 변환 중...")
        markdown = convert_page(page, blocks)

        if stdout:
            progress.stop()
            console.print(markdown)
            return

        # 출력 파일명 결정
        if not output:
            title = client.get_page_title(page)
            safe_title = "".join(
                c for c in title if c not in r'\/:*?"<>|'
            ).strip() or "notion_export"
            output = f"{safe_title}.md"

        progress.update(task, description=f"💾 저장 중: {output}")
        Path(output).write_text(markdown, encoding="utf-8")
        progress.update(task, description="✅ 완료!")

    console.print(
        Panel(
            f"[bold green]✅ 추출 완료![/bold green]\n\n"
            f"[bold]블록 수:[/bold] {len(blocks)}\n"
            f"[bold]저장 위치:[/bold] {Path(output).resolve()}",
            title="md-notion pull",
            border_style="green",
        )
    )


# ------------------------------------------------------------------ #
# 배치 처리
# ------------------------------------------------------------------ #

@main.command("push-all")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--page-id", "-p", default=None, help="업로드할 Notion 부모 페이지 ID.")
@click.option("--pattern", default="*.md", show_default=True, help="파일 글로브 패턴.")
def push_all(directory: str, page_id: str | None, pattern: str) -> None:
    """디렉토리 내 마크다운 파일을 일괄 업로드합니다.

    \b
    예시:
      md-notion push-all ./docs --page-id abc123
      md-notion push-all ./posts --pattern "**/*.md"
    """
    client = _get_client()
    parent_id = page_id or config.default_page_id

    if not parent_id:
        err_console.print("❌ --page-id 또는 NOTION_DEFAULT_PAGE_ID가 필요합니다.")
        sys.exit(1)

    parent_id = NotionClient.extract_page_id(parent_id)
    files = sorted(Path(directory).glob(pattern))

    if not files:
        console.print(f"⚠️  [{directory}] 에서 [{pattern}] 파일을 찾을 수 없습니다.")
        return

    # 결과 테이블
    table = Table(title="📤 배치 업로드 결과", show_lines=True)
    table.add_column("파일", style="cyan")
    table.add_column("상태", justify="center")
    table.add_column("블록 수", justify="right")
    table.add_column("URL", style="dim")

    success = 0
    for file in files:
        try:
            blocks = convert_file(str(file))
            title = file.stem

            # 첫 H1 탐색
            content = file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            page = client.create_page(parent_id, title, children=blocks[:100])
            if len(blocks) > 100:
                client.append_blocks(page["id"], blocks[100:])

            url = f"https://www.notion.so/{page['id'].replace('-', '')}"
            table.add_row(file.name, "[green]✅ 성공[/green]", str(len(blocks)), url)
            success += 1

        except Exception as e:
            table.add_row(file.name, "[red]❌ 실패[/red]", "-", str(e))

    console.print(table)
    console.print(f"\n[bold]총 {len(files)}개 중 {success}개 성공[/bold]")