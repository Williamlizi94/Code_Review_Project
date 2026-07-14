"""Result deduplication and severity-based ranking."""

from app.analyzer.base import AnalyzerIssue, SEVERITY_ORDER


def merge_issues(issues: list[AnalyzerIssue]) -> list[AnalyzerIssue]:
    """Deduplicate and sort issues by severity.

    Deduplication key: (file_path, line_start, rule_id or message[:80])
    When duplicates exist, prefer the one from the LLM source (has suggestions),
    otherwise keep the first occurrence.
    """
    seen: dict[tuple, AnalyzerIssue] = {}

    for issue in issues:
        key = issue.dedup_key()
        if key not in seen:
            seen[key] = issue
        else:
            existing = seen[key]
            # Prefer issue with suggestion (typically from LLM)
            if issue.suggestion and not existing.suggestion:
                seen[key] = issue
            # Prefer higher severity
            elif SEVERITY_ORDER.get(issue.severity, 99) < SEVERITY_ORDER.get(
                existing.severity, 99
            ):
                seen[key] = issue

    unique = list(seen.values())
    # Sort by severity (Critical first), then by file and line
    unique.sort(
        key=lambda i: (
            SEVERITY_ORDER.get(i.severity, 99),
            i.file_path or "",
            i.line_start or 0,
        )
    )
    return unique
