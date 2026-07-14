"""LangChain @tool for running language-specific linters."""

import asyncio
import json
from pathlib import Path

from langchain_core.tools import tool

from app.analyzer.bandit import BanditAnalyzer
from app.analyzer.eslint import ESLintAnalyzer
from app.analyzer.staticcheck import StaticcheckAnalyzer


@tool
def run_linters(path: str, language: str) -> str:
    """Run language-specific linters on the given path.

    Args:
        path: Absolute path to file or directory.
        language: Programming language (python, javascript, typescript, go).

    Returns:
        JSON string with list of linter issues.
    """
    lang = language.lower()
    loop = asyncio.new_event_loop()

    try:
        if lang == "python":
            issues = loop.run_until_complete(BanditAnalyzer().analyze(path))
        elif lang in ("javascript", "typescript"):
            issues = loop.run_until_complete(ESLintAnalyzer().analyze(path))
        elif lang == "go":
            issues = loop.run_until_complete(StaticcheckAnalyzer().analyze(path))
        else:
            return json.dumps({"info": f"No language-specific linter for {language!r}"})
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
