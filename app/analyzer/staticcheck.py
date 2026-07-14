import asyncio
import json

from loguru import logger

from app.analyzer.base import AnalyzerIssue, BaseAnalyzer
from app.config import get_settings

settings = get_settings()


class StaticcheckAnalyzer(BaseAnalyzer):
    """Go static analyzer using staticcheck."""

    name = "staticcheck"

    def is_enabled(self) -> bool:
        return settings.analyzer_staticcheck_enabled

    async def analyze(self, path: str, **kwargs) -> list[AnalyzerIssue]:
        if not self.is_enabled():
            return []

        cmd = ["staticcheck", "-f", "json", "./..."]

        logger.info(f"Running Staticcheck on {path!r}")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)
        except asyncio.TimeoutError:
            logger.warning("Staticcheck timed out")
            return []
        except FileNotFoundError:
            logger.warning("staticcheck not found in PATH — skipping")
            return []

        issues: list[AnalyzerIssue] = []
        # staticcheck outputs one JSON object per line
        for line in stdout.decode().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            code = obj.get("code", "")
            # SA = static analysis checks, S1 = simplifications, ST = style, QF = quickfixes
            category = "maintainability"
            if code.startswith("SA"):
                category = "security" if "unsafe" in code.lower() else "maintainability"
            elif code.startswith("ST"):
                category = "style"

            pos = obj.get("position", {})
            issues.append(
                AnalyzerIssue(
                    severity="MEDIUM",
                    source=self.name,
                    message=obj.get("message", ""),
                    file_path=pos.get("file"),
                    line_start=pos.get("line"),
                    rule_id=code,
                    category=category,
                )
            )

        logger.info(f"Staticcheck found {len(issues)} issues")
        return issues
