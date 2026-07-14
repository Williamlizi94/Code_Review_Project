import asyncio
import json

from loguru import logger

from app.analyzer.base import AnalyzerIssue, BaseAnalyzer
from app.config import get_settings

settings = get_settings()

_SEVERITY_MAP = {
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
}


class BanditAnalyzer(BaseAnalyzer):
    """Python security scanner using Bandit."""

    name = "bandit"

    def is_enabled(self) -> bool:
        return settings.analyzer_bandit_enabled

    async def analyze(self, path: str, **kwargs) -> list[AnalyzerIssue]:
        if not self.is_enabled():
            return []

        cmd = [
            "bandit",
            "-r",
            "-f", "json",
            "-q",
            path,
        ]

        logger.info(f"Running Bandit on {path!r}")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            logger.warning("Bandit timed out")
            return []
        except FileNotFoundError:
            logger.warning("bandit not found in PATH — skipping")
            return []

        # Bandit exits 1 when issues found, 0 when none
        if proc.returncode > 1:
            logger.warning(f"Bandit error: {stderr.decode()}")
            return []

        try:
            data = json.loads(stdout.decode())
        except json.JSONDecodeError:
            return []

        issues: list[AnalyzerIssue] = []
        for result in data.get("results", []):
            raw_sev = result.get("issue_severity", "MEDIUM").upper()
            severity = _SEVERITY_MAP.get(raw_sev, "MEDIUM")  # type: ignore[assignment]
            issues.append(
                AnalyzerIssue(
                    severity=severity,
                    source=self.name,
                    message=result.get("issue_text", ""),
                    file_path=result.get("filename"),
                    line_start=result.get("line_number"),
                    rule_id=result.get("test_id"),
                    category="security",
                    metadata={
                        "test_name": result.get("test_name"),
                        "confidence": result.get("issue_confidence"),
                        "code": result.get("code", ""),
                        "cwe": result.get("issue_cwe", {}).get("id"),
                    },
                )
            )

        logger.info(f"Bandit found {len(issues)} issues")
        return issues
