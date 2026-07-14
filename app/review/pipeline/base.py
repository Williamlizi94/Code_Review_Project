"""Base pipeline stage and shared context dataclass."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.analyzer.base import AnalyzerIssue


@dataclass
class PipelineContext:
    """Shared mutable state passed through the review pipeline."""

    review_id: uuid.UUID
    review_type: str              # GIT_REPO | DIRECTORY | FILE | SNIPPET
    target: str | None            # repo URL or local path
    branch: str | None
    mode: str                     # FULL | INCREMENTAL
    languages: list[str] | None
    ruleset_id: str | None
    notify_webhook: str | None
    snippet_content: str | None
    snippet_language: str | None

    # Set during pipeline execution
    workspace_path: str | None = None
    diff_text: str | None = None
    static_issues: list[AnalyzerIssue] = field(default_factory=list)
    llm_issues: list[dict[str, Any]] = field(default_factory=list)
    merged_issues: list[AnalyzerIssue] = field(default_factory=list)
    rag_context: str | None = None
    report_html: str | None = None
    report_markdown: str | None = None
    error: str | None = None


class PipelineStage(ABC):
    """Abstract base for a review pipeline stage."""

    name: str = "base"

    @abstractmethod
    async def run(self, ctx: PipelineContext) -> PipelineContext:
        """Execute this stage and return the updated context."""
        ...

    async def __call__(self, ctx: PipelineContext) -> PipelineContext:
        return await self.run(ctx)
