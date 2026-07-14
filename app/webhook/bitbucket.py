"""Bitbucket webhook handler."""

import hashlib
import hmac

from fastapi import HTTPException, Request, status
from loguru import logger

from app.config import get_settings

settings = get_settings()


def verify_bitbucket_signature(payload: bytes, signature_header: str | None) -> None:
    """Validate Bitbucket's X-Hub-Signature header (HMAC-SHA256)."""
    if not settings.bitbucket_webhook_secret:
        return
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Hub-Signature header",
        )
    expected = "sha256=" + hmac.new(
        settings.bitbucket_webhook_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Bitbucket webhook signature",
        )


async def handle_bitbucket_event(request: Request) -> dict:
    """Parse and handle a Bitbucket webhook event."""
    payload_bytes = await request.body()
    sig = request.headers.get("X-Hub-Signature")
    verify_bitbucket_signature(payload_bytes, sig)

    event_key = request.headers.get("X-Event-Key", "")
    try:
        import json
        payload = json.loads(payload_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info(f"Bitbucket event received: {event_key!r}")

    if event_key in ("pullrequest:created", "pullrequest:updated"):
        pr = payload.get("pullrequest", {})
        repo = payload.get("repository", {})
        source = pr.get("source", {})
        return {
            "action": "review",
            "platform": "bitbucket",
            "repo_url": repo.get("links", {}).get("clone", [{}])[0].get("href", ""),
            "branch": source.get("branch", {}).get("name", ""),
            "pr_id": pr.get("id"),
            "commit_sha": source.get("commit", {}).get("hash"),
            "mode": "INCREMENTAL",
        }

    return {"action": "ignored", "reason": f"Event {event_key!r} not handled"}
