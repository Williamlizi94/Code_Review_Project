import asyncio
import json
import os
import tempfile
from pathlib import Path

from loguru import logger

from app.analyzer.base import AnalyzerIssue, BaseAnalyzer, normalize_severity
from app.config import get_settings

settings = get_settings()


class SemgrepAnalyzer(BaseAnalyzer):
    name = "semgrep"

    def is_enabled(self) -> bool:
        return settings.analyzer_semgrep_enabled

    async def analyze(
        self,
        path: str,
        rules: list[str] | None = None,
        languages: list[str] | None = None,
        **kwargs,
    ) -> list[AnalyzerIssue]:
        if not self.is_enabled():
            return []

        rules = rules or settings.semgrep_rules_list
        rules_arg = ",".join(rules)

        cmd = [
            "semgrep",
            "--json",
            "--no-git-ignore",
            f"--config={rules_arg}",
            path,
        ]
        if languages:
            for lang in languages:
                cmd += ["--lang", lang]

        logger.info(f"Running Semgrep on {path!r} with rules: {rules_arg}")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path if os.path.isdir(path) else None,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        except asyncio.TimeoutError:
            logger.warning("Semgrep timed out after 300 seconds")
            return []
        except FileNotFoundError:
            logger.warning("semgrep not found in PATH — skipping")
            return []

        if proc.returncode not in (0, 1):  # 1 = findings found
            logger.warning(f"Semgrep exited with code {proc.returncode}: {stderr.decode()}")
            return []

        try:
            data = json.loads(stdout.decode())
        except json.JSONDecodeError:
            logger.warning("Failed to parse Semgrep JSON output")
            return []

        issues: list[AnalyzerIssue] = []
        for result in data.get("results", []):
            extra = result.get("extra", {})
            meta = result.get("check_id", "")
            severity_raw = extra.get("severity", "WARNING")
            # Semgrep SARIF-level severity: ERROR→HIGH, WARNING→MEDIUM, INFO→INFO
            severity = normalize_severity(severity_raw)
            # Override with metadata if available
            if extra.get("metadata", {}).get("impact", "").upper() in (
                "CRITICAL", "HIGH", "MEDIUM", "LOW"
            ):
                severity = extra["metadata"]["impact"].upper()  # type: ignore[assignment]

            start = result.get("start", {})
            end = result.get("end", {})
            issues.append(
                AnalyzerIssue(
                    severity=severity,
                    source=self.name,
                    message=extra.get("message", ""),
                    file_path=result.get("path"),
                    line_start=start.get("line"),
                    line_end=end.get("line"),
                    rule_id=meta,
                    category=_map_semgrep_category(meta),
                    metadata={
                        "code": extra.get("lines", ""),
                        "cwe": extra.get("metadata", {}).get("cwe"),
                        "owasp": extra.get("metadata", {}).get("owasp"),
                    },
                )
            )

        logger.info(f"Semgrep found {len(issues)} issues")
        return issues


def _map_semgrep_category(rule_id: str) -> str:
    """Heuristic category mapping from Semgrep rule ID."""
    rid = rule_id.lower()
    if any(k in rid for k in ("inject", "xss", "ssrf", "secret", "auth", "crypto", "sqli", "owasp")):
        return "security"
    if any(k in rid for k in ("perf", "n+1", "memory", "async", "blocking")):
        return "performance"
    if any(k in rid for k in ("style", "format", "naming", "comment")):
        return "style"
    return "maintainability"
