from __future__ import annotations

# Notion이 지원하는 언어 목록 (지원 외 언어는 plain text로 대체)
SUPPORTED_LANGUAGES = {
    "abap", "arduino", "bash", "basic", "c", "clojure", "coffeescript",
    "c++", "c#", "css", "dart", "diff", "docker", "elixir", "elm",
    "erlang", "flow", "fortran", "f#", "gherkin", "glsl", "go", "graphql",
    "groovy", "haskell", "html", "java", "javascript", "json", "julia",
    "kotlin", "latex", "less", "lisp", "livescript", "lua", "makefile",
    "markdown", "markup", "matlab", "mermaid", "nix", "objective-c", "ocaml",
    "pascal", "perl", "php", "plain text", "powershell", "prolog",
    "protobuf", "python", "r", "reason", "ruby", "rust", "sass", "scala",
    "scheme", "scss", "shell", "sql", "swift", "typescript", "vb.net",
    "verilog", "vhdl", "visual basic", "webassembly", "xml", "yaml",
    "java/c/c++/c#",
}


def build_code_block(code: str, language: str = "") -> dict:
    """코드블록 Notion 블록 생성"""
    lang = language.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "plain text"
    
    # 빈 코드블록 안전 처리
    content = code if code.strip() else " "
    
    return {
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": content}}],
            "language": lang,
        },
    }


def parse_code_block(block: dict) -> str:
    """Notion 코드블록 → 마크다운 코드블록 (들여쓰기 보정 포함)"""
    lang = block["code"].get("language", "plain text")
    if lang == "plain text":
        lang = ""
    code = "".join(
        t["plain_text"] for t in block["code"].get("rich_text", [])
    )
    # Notion이 들여쓰기를 단일 공백으로 압축하는 경우 보정 시도
    # 단순 1공백 → 4공백 복원 (Python/Java 등 일반적인 경우)
    if lang in ("python", "java", "javascript", "typescript", "c", "c++", "c#"):
        code = _restore_indent(code)
    return f"```{lang}\n{code}\n```"


def _restore_indent(code: str) -> str:
    """Notion에서 뭉개진 들여쓰기 복원 시도 (1칸 → 4칸)"""
    lines = code.splitlines()
    restored = []
    for line in lines:
        # 줄 시작이 단일 공백인 경우만 4칸으로 복원
        stripped = line.lstrip(" ")
        space_count = len(line) - len(stripped)
        if space_count > 0:
            restored.append("    " * space_count + stripped)
        else:
            restored.append(line)
    return "\n".join(restored)