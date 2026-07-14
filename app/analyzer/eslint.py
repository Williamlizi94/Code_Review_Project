import asyncio
import json

from loguru import logger

from app.analyzer.base import AnalyzerIssue, BaseAnalyzer
from app.config import get_settings

settings = get_settings()

# ESLint severity: 1 = warning, 2 = error
_SEVERITY_MAP = {1: "MEDIUM", 2: "HIGH"}


class ESLintAnalyzer(BaseAnalyzer):
    """JavaScript / TypeScript linter using ESLint."""

    name = "eslint"

    def is_enabled(self) -> bool:
        return settings.analyzer_eslint_enabled

    async def analyze(self, path: str, **kwargs) -> list[AnalyzerIssue]:
        if not self.is_enabled():
            return []

        cmd = [
            "eslint",
            "--format", "json",
            "--no-eslintrc",
            "--env", "es2021,browser,node",
            path,
        ]

        logger.info(f"Running ESLint on {path!r}")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            logger.warning("ESLint timed out")
            return []
        except FileNotFoundError:
            logger.warning("eslint not found in PATH — skipping")
            return []

        try:
            data = json.loads(stdout.decode() or "[]")
        except json.JSONDecodeError:
            return []

        issues: list[AnalyzerIssue] = []
        for file_result in data:
            file_path = file_result.get("filePath", "")
            for msg in file_result.get("messages", []):
                sev_int = msg.get("severity", 1)
                severity = _SEVERITY_MAP.get(sev_int, "MEDIUM")  # type: ignore[assignment]
                rule_id = msg.get("ruleId", "")
                issues.append(
                    AnalyzerIssue(
                        severity=severity,
                        source=self.name,
                        message=msg.get("message", ""),
                        file_path=file_path,
                        line_start=msg.get("line"),
                        line_end=msg.get("endLine"),
                        rule_id=rule_id,
                        category=_map_eslint_category(rule_id),
                    )
                )

        logger.info(f"ESLint found {len(issues)} issues")
        return issues


def _map_eslint_category(rule_id: str) -> str:
    rid = rule_id.lower()
    if any(k in rid for k in ("security", "no-eval", "no-new-func", "prototype")):
        return "security"
    if any(k in rid for k in ("perf", "complexity")):
        return "performance"
    return "style"
