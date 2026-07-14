"""Unit tests for static analyzers (mocking subprocess)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.analyzer.bandit import BanditAnalyzer
from app.analyzer.semgrep import SemgrepAnalyzer


class MockProcess:
    def __init__(self, stdout: bytes, returncode: int = 0):
        self._stdout = stdout
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, b""


@pytest.mark.asyncio
async def test_semgrep_parses_json_output():
    sample_output = json.dumps({
        "results": [
            {
                "check_id": "python.lang.security.audit.sql-injection",
                "path": "app/views.py",
                "start": {"line": 42},
                "end": {"line": 42},
                "extra": {
                    "message": "Potential SQL injection",
                    "severity": "ERROR",
                    "lines": "cursor.execute(query)",
                },
            }
        ]
    }).encode()

    mock_proc = MockProcess(sample_output, returncode=1)
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with patch("asyncio.wait_for", return_value=(sample_output, b"")):
            analyzer = SemgrepAnalyzer()
            issues = await analyzer.analyze("/tmp/test")

    assert len(issues) == 1
    assert issues[0].source == "semgrep"
    assert issues[0].file_path == "app/views.py"
    assert issues[0].line_start == 42


@pytest.mark.asyncio
async def test_semgrep_handles_empty_results():
    sample_output = json.dumps({"results": []}).encode()
    mock_proc = MockProcess(sample_output, returncode=0)

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with patch("asyncio.wait_for", return_value=(sample_output, b"")):
            analyzer = SemgrepAnalyzer()
            issues = await analyzer.analyze("/tmp/test")

    assert issues == []


@pytest.mark.asyncio
async def test_bandit_parses_json_output():
    sample_output = json.dumps({
        "results": [
            {
                "test_id": "B101",
                "test_name": "assert_used",
                "issue_text": "Use of assert detected.",
                "issue_severity": "LOW",
                "issue_confidence": "HIGH",
                "filename": "app/utils.py",
                "line_number": 15,
                "code": "assert x > 0",
                "issue_cwe": {"id": 703},
            }
        ]
    }).encode()

    mock_proc = MockProcess(sample_output, returncode=1)
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with patch("asyncio.wait_for", return_value=(sample_output, b"")):
            analyzer = BanditAnalyzer()
            issues = await analyzer.analyze("/tmp/test")

    assert len(issues) == 1
    assert issues[0].rule_id == "B101"
    assert issues[0].category == "security"
    assert issues[0].line_start == 15


@pytest.mark.asyncio
async def test_semgrep_disabled_returns_empty():
    from app.config import get_settings
    settings = get_settings()
    original = settings.analyzer_semgrep_enabled
    settings.analyzer_semgrep_enabled = False

    try:
        analyzer = SemgrepAnalyzer()
        assert not analyzer.is_enabled()
        issues = await analyzer.analyze("/tmp/test")
        assert issues == []
    finally:
        settings.analyzer_semgrep_enabled = original


@pytest.mark.asyncio
async def test_semgrep_not_found_returns_empty():
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
        analyzer = SemgrepAnalyzer()
        issues = await analyzer.analyze("/tmp/test")
    assert issues == []
