"""Review orchestration service — assembles and runs the pipeline."""

import uuid
from typing import Any

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.base import SEVERITY_ORDER
from app.config import get_settings
from app.models.review import Review, ReviewIssue, ReviewReport
from app.review.pipeline import (
    ASTParseStage,
    GitCloneStage,
    LLMReviewStage,
    NotifyStage,
    PipelineContext,
    RAGRetrievalStage,
    ReportGenerateStage,
    ResultMergeStage,
    StaticAnalysisStage,
)

settings = get_settings()


async def run_review_pipeline(review_id: uuid.UUID, db: AsyncSession) -> None:
    """Execute the full 8-stage review pipeline for a given review task.

    Updates the Review record in the database throughout execution.
    """
    # Load review from DB
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if review is None:
        logger.error(f"Review {review_id} not found")
        return

    await _update_status(review_id, "RUNNING", db)

    ctx = PipelineContext(
        review_id=review_id,
        review_type=review.type,
        target=review.target,
        branch=review.branch,
        mode=review.mode,
        languages=review.languages,
        ruleset_id=review.ruleset_id,
        notify_webhook=review.notify_webhook,
        snippet_content=review.snippet_content,
        snippet_language=None,  # could be stored as extra field
    )

    # ── Run stages sequentially ───────────────────────────────────────
    stages = [
        GitCloneStage(),
        StaticAnalysisStage(),
        ASTParseStage(),
        RAGRetrievalStage(db),
        LLMReviewStage(),
        ResultMergeStage(),
        ReportGenerateStage(),
        NotifyStage(),
    ]

    for stage in stages:
        try:
            ctx = await stage(ctx)
            # Update workspace path after clone
            if stage.name == "git_clone" and ctx.workspace_path:
                await db.execute(
                    update(Review)
                    .where(Review.id == review_id)
                    .values(workspace_path=ctx.workspace_path)
                )
                await db.commit()
        except Exception as exc:
            logger.error(f"Pipeline stage {stage.name!r} raised unexpected error: {exc}")
            ctx.error = str(exc)
            break

    # ── Persist results ───────────────────────────────────────────────
    if ctx.error:
        await _update_status(review_id, "FAILED", db, error_message=ctx.error)
        return

    # Save issues
    issue_objs = [
        ReviewIssue(
            review_id=review_id,
            severity=i.severity,
            source=i.source,
            rule_id=i.rule_id,
            file_path=i.file_path,
            line_start=i.line_start,
            line_end=i.line_end,
            message=i.message,
            suggestion=i.suggestion,
            category=i.category,
            extra_metadata=i.metadata,
        )
        for i in ctx.merged_issues
    ]
    db.add_all(issue_objs)

    # Save reports
    if ctx.report_html:
        db.add(ReviewReport(review_id=review_id, format="html", content=ctx.report_html))
    if ctx.report_markdown:
        db.add(
            ReviewReport(review_id=review_id, format="markdown", content=ctx.report_markdown)
        )

    # Compute stats
    critical = sum(1 for i in ctx.merged_issues if i.severity == "CRITICAL")
    high = sum(1 for i in ctx.merged_issues if i.severity == "HIGH")

    # Quality gate
    gate_status = "SKIPPED"
    if settings.quality_gate_enabled:
        gate_status = "PASS"
        if critical >= settings.quality_gate_fail_on_critical:
            gate_status = "FAIL"
        elif high >= settings.quality_gate_fail_on_high:
            gate_status = "FAIL"

    await db.execute(
        update(Review)
        .where(Review.id == review_id)
        .values(
            status="COMPLETED",
            issues_count=len(ctx.merged_issues),
            critical_count=critical,
            high_count=high,
            quality_gate_status=gate_status,
            error_message=None,
        )
    )
    await db.commit()
    logger.info(
        f"Review {review_id} COMPLETED: {len(ctx.merged_issues)} issues, "
        f"gate={gate_status}"
    )


async def _update_status(
    review_id: uuid.UUID,
    status: str,
    db: AsyncSession,
    error_message: str | None = None,
) -> None:
    values: dict[str, Any] = {"status": status}
    if error_message is not None:
        values["error_message"] = error_message
    await db.execute(update(Review).where(Review.id == review_id).values(**values))
    await db.commit()
