"""Stage 2: Run static analyzers in parallel."""

import asyncio
import os
import tempfile

from loguru import logger

from app.analyzer.bandit import BanditAnalyzer
from app.analyzer.eslint import ESLintAnalyzer
from app.analyzer.semgrep import SemgrepAnalyzer
from app.analyzer.staticcheck import StaticcheckAnalyzer
from app.config import get_settings
from app.review.pipeline.base import PipelineContext, PipelineStage

settings = get_settings()


class StaticAnalysisStage(PipelineStage):
    name = "static_analysis"

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.error:
            return ctx

        # Determine analysis path
        if ctx.review_type == "SNIPPET":
            # Write snippet to a temp file
            path = await _write_snippet_to_file(
                ctx.snippet_content or "", ctx.snippet_language
            )
        elif ctx.workspace_path:
            path = ctx.workspace_path
        elif ctx.target and os.path.exists(ctx.target):
            path = ctx.target
        else:
            logger.warning("[Stage 2] No valid path for static analysis")
            return ctx

        languages = ctx.languages or []
        logger.info(f"[Stage 2] Static analysis on {path!r}")

        tasks = []
        # Semgrep: always run (multi-language)
        tasks.append(SemgrepAnalyzer().analyze(path, languages=languages or None))

        # Language-specific linters
        is_python = not languages or "python" in languages
        is_js_ts = not languages or any(l in languages for l in ("javascript", "typescript"))
        is_go = not languages or "go" in languages

        if is_python:
            tasks.append(BanditAnalyzer().analyze(path))
        if is_js_ts:
            tasks.append(ESLintAnalyzer().analyze(path))
        if is_go:
            tasks.append(StaticcheckAnalyzer().analyze(path))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_issues = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"[Stage 2] Analyzer error: {result}")
            else:
                all_issues.extend(result)

        ctx.static_issues = all_issues
        logger.info(f"[Stage 2] Found {len(all_issues)} static issues")
        return ctx


async def _write_snippet_to_file(content: str, language: str | None) -> str:
    """Write a code snippet to a temp file and return its path."""
    ext_map = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "go": ".go",
        "rust": ".rs",
        "java": ".java",
        "ruby": ".rb",
        "php": ".php",
    }
    ext = ext_map.get((language or "").lower(), ".txt")
    fd, path = tempfile.mkstemp(suffix=ext, prefix="snippet_")
    os.write(fd, content.encode())
    os.close(fd)
    return path
