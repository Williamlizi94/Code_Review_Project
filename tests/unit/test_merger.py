"""Unit tests for the result merger (deduplication + ranking)."""

import pytest

from app.analyzer.base import AnalyzerIssue
from app.review.merger import merge_issues


def make_issue(severity="MEDIUM", source="semgrep", file_path="foo.py", line=10, rule_id="r1", msg="test", suggestion=None):
    return AnalyzerIssue(
        severity=severity,
        source=source,
        message=msg,
        file_path=file_path,
        line_start=line,
        rule_id=rule_id,
        suggestion=suggestion,
    )


def test_deduplication_removes_exact_duplicates():
    issues = [
        make_issue(),
        make_issue(),  # duplicate
    ]
    merged = merge_issues(issues)
    assert len(merged) == 1


def test_deduplication_keeps_different_lines():
    issues = [
        make_issue(line=10),
        make_issue(line=20),
    ]
    merged = merge_issues(issues)
    assert len(merged) == 2


def test_sorting_critical_before_high():
    issues = [
        make_issue(severity="HIGH"),
        make_issue(severity="CRITICAL", line=20),
        make_issue(severity="LOW", line=30),
    ]
    merged = merge_issues(issues)
    assert merged[0].severity == "CRITICAL"
    assert merged[1].severity == "HIGH"
    assert merged[2].severity == "LOW"


def test_prefer_suggestion_on_dedup():
    base = make_issue()
    with_suggestion = make_issue(source="llm", suggestion="Fix it!")
    merged = merge_issues([base, with_suggestion])
    assert len(merged) == 1
    assert merged[0].suggestion == "Fix it!"


def test_empty_issues():
    assert merge_issues([]) == []


def test_single_issue():
    issue = make_issue(severity="CRITICAL")
    merged = merge_issues([issue])
    assert len(merged) == 1
    assert merged[0].severity == "CRITICAL"
