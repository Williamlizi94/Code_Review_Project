"""Stage 8: Send notifications — webhook callbacks and PR/MR comments."""

import json

import httpx
from loguru import logger

from app.review.pipeline.base import PipelineContext, PipelineStage


class NotifyStage(PipelineStage):
    name = "notify"

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        # ── Webhook callback ──────────────────────────────────────────
        if ctx.notify_webhook:
            await _send_webhook(ctx)

        return ctx


async def _send_webhook(ctx: PipelineContext) -> None:
    """POST review summary to the configured CI/CD callback URL."""
    from app.analyzer.base import SEVERITY_ORDER

    payload = {
        "review_id": str(ctx.review_id),
        "status": "COMPLETED" if not ctx.error else "FAILED",
        "issues_count": len(ctx.merged_issues),
        "critical_count": sum(1 for i in ctx.merged_issues if i.severity == "CRITICAL"),
        "high_count": sum(1 for i in ctx.merged_issues if i.severity == "HIGH"),
        "error": ctx.error,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                ctx.notify_webhook,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            logger.info(f"[Stage 8] Webhook notified: {ctx.notify_webhook!r} → {resp.status_code}")
    except Exception as exc:
        logger.warning(f"[Stage 8] Webhook notification failed: {exc}")
