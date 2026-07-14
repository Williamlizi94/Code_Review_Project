"""Webhook receiver endpoints for GitHub, GitLab, and Bitbucket."""

from fastapi import APIRouter, BackgroundTasks, Request, status
from fastapi.responses import JSONResponse

from app.webhook.bitbucket import handle_bitbucket_event
from app.webhook.github import handle_github_event
from app.webhook.gitlab import handle_gitlab_event

router = APIRouter(prefix="/api/v1/webhook", tags=["Webhooks"])


@router.post("/github", status_code=status.HTTP_200_OK)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Receive GitHub push / pull_request events."""
    event_data = await handle_github_event(request)

    if event_data.get("action") == "review":
        background_tasks.add_task(_trigger_webhook_review, event_data)

    return JSONResponse(content={"status": "ok", "action": event_data.get("action")})


@router.post("/gitlab", status_code=status.HTTP_200_OK)
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Receive GitLab push / merge_request events."""
    event_data = await handle_gitlab_event(request)

    if event_data.get("action") == "review":
        background_tasks.add_task(_trigger_webhook_review, event_data)

    return JSONResponse(content={"status": "ok", "action": event_data.get("action")})


@router.post("/bitbucket", status_code=status.HTTP_200_OK)
async def bitbucket_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Receive Bitbucket push / pullrequest events."""
    event_data = await handle_bitbucket_event(request)

    if event_data.get("action") == "review":
        background_tasks.add_task(_trigger_webhook_review, event_data)

    return JSONResponse(content={"status": "ok", "action": event_data.get("action")})


async def _trigger_webhook_review(event_data: dict) -> None:
    """Create a Review record and enqueue the pipeline from a webhook event."""
    from app.database import AsyncSessionLocal
    from app.models.review import Review
    from app.worker import run_review_task

    async with AsyncSessionLocal() as db:
        review = Review(
            type="GIT_REPO",
            target=event_data.get("repo_url"),
            branch=event_data.get("branch"),
            mode=event_data.get("mode", "INCREMENTAL"),
            status="PENDING",
        )
        db.add(review)
        await db.flush()
        await db.commit()
        await db.refresh(review)

    try:
        run_review_task.delay(str(review.id))
    except Exception as exc:
        from loguru import logger
        logger.error(f"Failed to enqueue webhook review task: {exc}")
