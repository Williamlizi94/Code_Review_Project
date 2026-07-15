import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Review(Base, UUIDMixin, TimestampMixin):
    """Represents a code review task."""

    __tablename__ = "reviews"

    # Review type: GIT_REPO | DIRECTORY | FILE | SNIPPET
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Target: repo URL, directory path, file path, or None for snippet
    target: Mapped[str | None] = mapped_column(Text, nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Review mode: FULL | INCREMENTAL
    mode: Mapped[str] = mapped_column(String(20), default="FULL", nullable=False)
    # Status: PENDING | RUNNING | COMPLETED | FAILED
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False, index=True)
    # Detected or specified languages
    languages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Semgrep ruleset identifier
    ruleset_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Webhook URL for CI/CD callback
    notify_webhook: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Raw code snippet (for SNIPPET type)
    snippet_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Local workspace path (set after git clone)
    workspace_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Error message if status=FAILED
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Summary stats
    issues_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Quality gate result: PASS | FAIL | SKIPPED
    quality_gate_status: Mapped[str] = mapped_column(
        String(20), default="SKIPPED", nullable=False
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    user: Mapped["User | None"] = relationship("User", back_populates="reviews")
    issues: Mapped[list["ReviewIssue"]] = relationship(
        "ReviewIssue", back_populates="review", cascade="all, delete-orphan"
    )
    reports: Mapped[list["ReviewReport"]] = relationship(
        "ReviewReport", back_populates="review", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Review {self.id} type={self.type} status={self.status}>"


class ReviewIssue(Base, UUIDMixin, TimestampMixin):
    """A single issue found during code review."""

    __tablename__ = "review_issues"

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    # Severity: CRITICAL | HIGH | MEDIUM | LOW | INFO
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Source: semgrep | bandit | eslint | staticcheck | llm
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # AI-generated fix suggestion (before/after diff)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Extra metadata (e.g., code snippet, AST context)
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Category: style | security | performance | maintainability | business_logic
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    review: Mapped["Review"] = relationship("Review", back_populates="issues")

    def __repr__(self) -> str:
        return f"<ReviewIssue {self.severity} {self.file_path}:{self.line_start}>"


class ReviewReport(Base, UUIDMixin, TimestampMixin):
    """Generated report for a review."""

    __tablename__ = "review_reports"

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    # Format: html | markdown | pdf
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    # Inline content (for html/markdown) or S3 path (for pdf)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    review: Mapped["Review"] = relationship("Review", back_populates="reports")
