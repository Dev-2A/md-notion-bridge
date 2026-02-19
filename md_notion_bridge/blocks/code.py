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
    
    return {
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": code}}],
            "language": lang,
        },
    }


def parse_code_block(block: dict) -> str:
    """Notion 코드 블록 → 마크다운 코드블록"""
    lang = block["code"].get("language", "plain text")
    if lang == "plain text":
        lang = ""
    code = "".join(
        t["plain_text"] for t in block["code"].get("rich_text", [])
    )
    return f"```{lang}\n{code}\n```"