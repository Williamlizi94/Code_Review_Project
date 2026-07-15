"""Review API endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.service import get_current_user
from app.database import get_db
from app.models.review import Review, ReviewReport
from app.models.user import User
from app.report.pdf import generate_pdf_report
from app.schemas.review import (
    IssueOut,
    ReviewDetailResponse,
    ReviewListResponse,
    ReviewRequest,
    ReviewResponse,
)

router = APIRouter(prefix="/api/v1/reviews", tags=["Reviews"])


def _review_access_filter(review_id: uuid.UUID, current_user: User):
    clauses = [Review.id == review_id]
    if not current_user.is_superuser:
        clauses.append(Review.user_id == current_user.id)
    return and_(*clauses)


async def _get_accessible_review(
    db: AsyncSession,
    review_id: uuid.UUID,
    current_user: User,
    include_issues: bool = False,
) -> Review | None:
    stmt = select(Review).where(_review_access_filter(review_id, current_user))
    if include_issues:
        stmt = stmt.options(selectinload(Review.issues))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewResponse:
    """Submit a new code review task. Processing happens asynchronously."""
    if request.type == "SNIPPET" and not request.snippet_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="snippet_content is required for SNIPPET review type",
        )

    review = Review(
        type=request.type,
        target=request.target,
        branch=request.branch,
        mode=request.mode,
        languages=request.languages,
        ruleset_id=request.ruleset_id,
        notify_webhook=str(request.notify_webhook) if request.notify_webhook else None,
        snippet_content=request.snippet_content,
        user_id=current_user.id,
        status="PENDING",
    )
    db.add(review)
    await db.flush()
    await db.commit()
    await db.refresh(review)

    background_tasks.add_task(_trigger_celery_task, str(review.id))

    return ReviewResponse.model_validate(review)


async def _trigger_celery_task(review_id: str) -> None:
    """Trigger the Celery review task and avoid surfacing infra failures to clients."""
    try:
        from app.worker import run_review_task

        run_review_task.apply_async(args=(review_id,), ignore_result=True, retry=False)
    except Exception as exc:
        from loguru import logger

        from app.database import AsyncSessionLocal

        logger.error(f"Failed to enqueue Celery task for review {review_id}: {exc}")
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Review)
                    .where(Review.id == uuid.UUID(review_id))
                    .values(status="FAILED", error_message=f"Celery enqueue failed: {exc}")
                )
                await db.commit()
        except Exception as status_exc:
            logger.error(
                f"Could not mark review {review_id} as FAILED after Celery enqueue error: "
                f"{status_exc}"
            )


@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewDetailResponse:
    """Get review status and issues for the current user."""
    review = await _get_accessible_review(db, review_id, current_user, include_issues=True)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    resp = ReviewDetailResponse.model_validate(review)
    resp.issues = [IssueOut.model_validate(i) for i in review.issues]
    return resp


@router.get("/{review_id}/report")
async def get_report(
    review_id: uuid.UUID,
    format: str = Query("html", description="Report format: html | markdown | pdf"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Download a review report in the requested format."""
    include_issues = format == "pdf"
    review = await _get_accessible_review(db, review_id, current_user, include_issues)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    if format in ("html", "markdown"):
        result = await db.execute(
            select(ReviewReport).where(
                and_(ReviewReport.review_id == review_id, ReviewReport.format == format)
            )
        )
        report = result.scalar_one_or_none()
        if not report or not report.content:
            raise HTTPException(status_code=404, detail=f"{format.title()} report not yet generated")
        if format == "html":
            return HTMLResponse(content=report.content)
        return PlainTextResponse(content=report.content, media_type="text/markdown")

    if format == "pdf":
        from app.analyzer.base import AnalyzerIssue

        issues = [
            AnalyzerIssue(
                severity=i.severity,
                source=i.source,
                message=i.message,
                file_path=i.file_path,
                line_start=i.line_start,
                rule_id=i.rule_id,
                category=i.category,
                suggestion=i.suggestion,
            )
            for i in review.issues
        ]
        pdf_bytes = generate_pdf_report(str(review_id), issues, target=review.target)
        if pdf_bytes is None:
            raise HTTPException(
                status_code=503,
                detail="PDF generation unavailable (WeasyPrint not installed)",
            )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="review-{review_id}.pdf"'},
        )

    raise HTTPException(status_code=400, detail=f"Unknown format {format!r}")


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, description="Search in target URL"),
    severity: str | None = Query(None, description="Filter by issue severity"),
    lang: str | None = Query(None, description="Filter by language"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewListResponse:
    """List review history with filtering and pagination."""
    stmt = select(Review)
    if not current_user.is_superuser:
        stmt = stmt.where(Review.user_id == current_user.id)

    if keyword:
        stmt = stmt.where(
            or_(
                Review.target.ilike(f"%{keyword}%"),
                Review.branch.ilike(f"%{keyword}%"),
            )
        )
    if status:
        stmt = stmt.where(Review.status == status.upper())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Review.created_at.desc()).offset(page * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()

    return ReviewListResponse(
        total=total,
        page=page,
        size=size,
        items=[ReviewResponse.model_validate(r) for r in rows],
    )
