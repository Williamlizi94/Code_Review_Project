import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import Settings
from app.review.pipeline.base import PipelineContext
from app.review.service import _cleanup_temporary_paths
from app.schemas.review import ReviewRequest
from app.webhook.github import verify_github_signature


def test_production_rejects_default_jwt_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(app_env="production", jwt_secret="change-me-in-production")


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/hook",
        "http://127.0.0.1/hook",
        "http://10.0.0.1/hook",
        "file:///etc/passwd",
        "https://user:password@example.com/hook",
    ],
)
def test_review_request_rejects_unsafe_callback_urls(url: str):
    with pytest.raises(ValidationError):
        ReviewRequest(type="SNIPPET", snippet_content="x = 1", notify_webhook=url)


def test_review_request_accepts_public_https_callback():
    request = ReviewRequest(
        type="SNIPPET",
        snippet_content="x = 1",
        notify_webhook="https://example.com/hook",
    )
    assert request.notify_webhook == "https://example.com/hook"


def test_github_webhook_fails_closed_without_secret(monkeypatch):
    from app.webhook import github

    monkeypatch.setattr(github.settings, "github_webhook_secret", "")
    with pytest.raises(HTTPException) as exc_info:
        verify_github_signature(b"{}", None)
    assert exc_info.value.status_code == 503


def test_review_request_normalizes_language_hints():
    request = ReviewRequest(
        type="SNIPPET",
        snippet_content="x = 1",
        snippet_language=" Python ",
        languages=["Python", " python ", "TypeScript"],
    )
    assert request.snippet_language == "python"
    assert request.languages == ["python", "typescript"]


def test_pipeline_cleanup_removes_only_recorded_temp_paths():
    temp_dir = Path(tempfile.mkdtemp(prefix="codeguardian_test_"))
    temp_file = temp_dir / "source.py"
    temp_file.write_text("x = 1", encoding="utf-8")
    context = PipelineContext(
        review_id=uuid.uuid4(),
        user_id=None,
        review_type="SNIPPET",
        target=None,
        branch=None,
        mode="FULL",
        languages=["python"],
        ruleset_id=None,
        notify_webhook=None,
        snippet_content="x = 1",
        snippet_language="python",
        temporary_paths=[str(temp_dir)],
    )

    _cleanup_temporary_paths(context)

    assert not temp_dir.exists()
    assert context.temporary_paths == []
