"""Markdown report generator."""

from collections import Counter
from datetime import datetime

from app.analyzer.base import AnalyzerIssue, SEVERITY_ORDER


def generate_markdown_report(
    review_id: str,
    issues: list[AnalyzerIssue],
    summary: str = "",
    target: str | None = None,
) -> str:
    counts = Counter(i.severity for i in issues)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        "# 🛡️ CodeGuardian AI — Code Review Report",
        "",
        f"**Review ID**: `{review_id}`  ",
        f"**Target**: {target or 'code snippet'}  ",
        f"**Generated**: {now}",
        "",
        "---",
        "",
        "## Summary Statistics",
        "",
        "| Severity | Count |",
        "|---|---|",
        f"| 🔴 CRITICAL | {counts.get('CRITICAL', 0)} |",
        f"| 🟠 HIGH | {counts.get('HIGH', 0)} |",
        f"| 🟡 MEDIUM | {counts.get('MEDIUM', 0)} |",
        f"| 🟢 LOW | {counts.get('LOW', 0)} |",
        f"| 🔵 INFO | {counts.get('INFO', 0)} |",
        f"| **Total** | **{len(issues)}** |",
        "",
    ]

    if summary:
        lines += [
            "## AI Analysis Summary",
            "",
            summary,
            "",
        ]

    if not issues:
        lines += ["## Issues", "", "✅ No issues found!", ""]
    else:
        lines += ["## Issues", ""]
        for idx, issue in enumerate(issues, 1):
            sev_icon = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢",
                "INFO": "🔵",
            }.get(issue.severity, "⚪")

            location = ""
            if issue.file_path:
                location = f"`{issue.file_path}`"
                if issue.line_start:
                    location += f":{issue.line_start}"

            lines += [
                f"### {idx}. {sev_icon} {issue.severity} — {issue.category or 'general'}",
                "",
                f"- **Source**: {issue.source}",
                f"- **Rule**: `{issue.rule_id or 'N/A'}`",
                f"- **Location**: {location or 'N/A'}",
                f"- **Message**: {issue.message}",
            ]

            if issue.suggestion:
                lines += [
                    "",
                    "**Suggestion**:",
                    "",
                    "```",
                    issue.suggestion,
                    "```",
                ]

            lines.append("")

    lines += [
        "---",
        "",
        "_🛡️ CodeGuardian AI — Every line of code, in every language, held to the highest standard._",
    ]

    return "\n".join(lines)
