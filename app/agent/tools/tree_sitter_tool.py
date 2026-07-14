"""LangChain @tool wrapper for Tree-sitter AST parsing."""

import json
from pathlib import Path

from langchain_core.tools import tool
from loguru import logger

# Language grammar mapping
_LANG_MAP = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "go": "go",
    "rs": "rust",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "rb": "ruby",
    "php": "php",
}


def _get_parser(language: str):
    """Return a Tree-sitter parser for the given language name."""
    try:
        import tree_sitter_languages
        return tree_sitter_languages.get_parser(language)
    except (ImportError, Exception):
        pass
    try:
        from tree_sitter import Language, Parser
        lang_obj = Language(f"build/{language}.so", language)
        parser = Parser()
        parser.set_language(lang_obj)
        return parser
    except Exception:
        return None


def _extract_functions(node, code_bytes: bytes) -> list[dict]:
    """Recursively extract function/method definitions from AST."""
    results = []
    func_types = {
        "function_definition",
        "function_declaration",
        "method_definition",
        "method_declaration",
        "arrow_function",
    }
    if node.type in func_types:
        name = None
        for child in node.children:
            if child.type in ("identifier", "property_identifier"):
                name = code_bytes[child.start_byte:child.end_byte].decode(errors="replace")
                break
        results.append(
            {
                "type": node.type,
                "name": name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
            }
        )
    for child in node.children:
        results.extend(_extract_functions(child, code_bytes))
    return results


@tool
def parse_ast(file_path: str) -> str:
    """Parse a source file using Tree-sitter and extract structural context.

    Args:
        file_path: Absolute path to the source file to parse.

    Returns:
        JSON string with extracted functions/classes and complexity hints.
    """
    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})

    ext = path.suffix.lstrip(".")
    lang = _LANG_MAP.get(ext)
    if not lang:
        return json.dumps({"error": f"Unsupported file extension: .{ext}"})

    parser = _get_parser(lang)
    if parser is None:
        return json.dumps({"error": f"Tree-sitter parser for {lang!r} not available"})

    try:
        code_bytes = path.read_bytes()
        tree = parser.parse(code_bytes)
        functions = _extract_functions(tree.root_node, code_bytes)
        return json.dumps(
            {
                "language": lang,
                "file": file_path,
                "functions": functions,
                "total_lines": code_bytes.count(b"\n") + 1,
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        logger.warning(f"AST parse error for {file_path}: {exc}")
        return json.dumps({"error": str(exc)})
