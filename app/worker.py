"""Celery application and review pipeline task."""

import asyncio
import uuid

from celery import Celery
from loguru import logger

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "codeguardian",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Retry on connection errors
    broker_connection_retry_on_startup=True,
)


@celery_app.task(
    name="codeguardian.run_review",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=1800,   # 30 min soft limit
    time_limit=2100,         # 35 min hard limit
)
def run_review_task(self, review_id: str) -> dict:
    """Celery task: run the full review pipeline for a given review ID."""
    logger.info(f"[Celery] Starting review pipeline for {review_id}")

    async def _run():
        from app.database import AsyncSessionLocal
        from app.review.service import run_review_pipeline

        async with AsyncSessionLocal() as db:
            await run_review_pipeline(uuid.UUID(review_id), db)

    try:
        asyncio.run(_run())
        logger.info(f"[Celery] Review pipeline completed for {review_id}")
        return {"review_id": review_id, "status": "completed"}
    except Exception as exc:
        logger.error(f"[Celery] Review pipeline failed for {review_id}: {exc}")
        raise self.retry(exc=exc)
