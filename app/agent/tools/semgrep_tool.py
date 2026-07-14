"""LangChain @tool wrapper around SemgrepAnalyzer."""

import asyncio
import json

from langchain_core.tools import tool

from app.analyzer.semgrep import SemgrepAnalyzer


@tool
def run_semgrep(path: str, ruleset: str = "p/owasp-top-ten", lang: str = "") -> str:
    """Run Semgrep static analysis on the given path.

    Args:
        path: Absolute path to the file or directory to scan.
        ruleset: Comma-separated Semgrep ruleset IDs (e.g., "p/owasp-top-ten,p/secrets").
        lang: Optional language filter (e.g., "python", "typescript").

    Returns:
        JSON string with a list of issues found.
    """
    analyzer = SemgrepAnalyzer()
    rules = [r.strip() for r in ruleset.split(",") if r.strip()]
    languages = [lang] if lang else None

    loop = asyncio.new_event_loop()
    try:
        issues = loop.run_until_complete(analyzer.analyze(path, rules=rules, languages=languages))
    finally:
        loop.close()

    result = [
        {
            "severity": i.severity,
            "rule_id": i.rule_id,
            "file_path": i.file_path,
            "line_start": i.line_start,
            "message": i.message,
            "category": i.category,
        }
        for i in issues
    ]
    return json.dumps(result, ensure_ascii=False)
