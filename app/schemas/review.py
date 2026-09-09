import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.security.url_validation import validate_public_http_url


class ReviewRequest(BaseModel):
    type: Literal["GIT_REPO", "DIRECTORY", "FILE", "SNIPPET"] = Field(
        ..., description="Review scope type"
    )
    target: str | None = Field(
        None,
        description="Repository URL, directory/file path. Leave empty for SNIPPET type.",
    )
    branch: str | None = Field(None, description="Git branch (for GIT_REPO type)")
    languages: list[str] | None = Field(
        None,
        description="Languages to analyze. Auto-detected if omitted.",
    )
    mode: Literal["FULL", "INCREMENTAL"] = Field(
        "FULL", description="FULL scan or INCREMENTAL (git diff only)"
    )
    ruleset_id: str | None = Field(None, description="Semgrep ruleset ID")
    notify_webhook: str | None = Field(
        None, description="CI/CD callback URL after review completes"
    )
    snippet_content: str | None = Field(
        None, description="Raw code snippet (required for SNIPPET type)"
    )
    snippet_language: str | None = Field(None, description="Language hint for snippet review")

    @field_validator("notify_webhook")
    @classmethod
    def validate_notify_webhook(cls, value: str | None) -> str | None:
        if value is not None:
            validate_public_http_url(value)
        return value

    @field_validator("languages")
    @classmethod
    def normalize_languages(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return sorted({language.strip().lower() for language in value if language.strip()})

    @field_validator("snippet_language")
    @classmethod
    def normalize_snippet_language(cls, value: str | None) -> str | None:
        return value.strip().lower() if value and value.strip() else None

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "GIT_REPO",
                "target": "https://github.com/org/repo.git",
                "branch": "feature/login",
                "languages": ["python", "typescript"],
                "mode": "INCREMENTAL",
                "ruleset_id": "owasp-top-ten",
            }
        }
    }


class IssueOut(BaseModel):
    id: uuid.UUID
    severity: str
    source: str
    rule_id: str | None
    file_path: str | None
    line_start: int | None
    line_end: int | None
    message: str
    suggestion: str | None
    category: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewResponse(BaseModel):
    id: uuid.UUID
    type: str
    target: str | None
    branch: str | None
    mode: str
    status: str
    languages: list[str] | None
    issues_count: int
    critical_count: int
    high_count: int
    quality_gate_status: str
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None

    model_config = {"from_attributes": True}


class ReviewDetailResponse(ReviewResponse):
    issues: list[IssueOut] = []


class ReviewListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[ReviewResponse]


class ReportOut(BaseModel):
    id: uuid.UUID
    review_id: uuid.UUID
    format: str
    content: str | None
    file_path: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
