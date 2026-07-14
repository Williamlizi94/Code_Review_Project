"""GitHub webhook handler."""

import hashlib
import hmac
import json

from fastapi import HTTPException, Request, status
from loguru import logger

from app.config import get_settings

settings = get_settings()


def verify_github_signature(payload: bytes, signature_header: str | None) -> None:
    """Validate GitHub's X-Hub-Signature-256 header."""
    if not settings.github_webhook_secret:
        return  # Signature verification disabled if secret not set
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Hub-Signature-256 header",
        )
    expected = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GitHub webhook signature",
        )


async def handle_github_event(request: Request) -> dict:
    """Parse and handle a GitHub webhook event.

    Returns a dict with review trigger parameters, or None if the event
    should not trigger a review.
    """
    payload_bytes = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")
    verify_github_signature(payload_bytes, sig)

    event_type = request.headers.get("X-GitHub-Event", "")
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info(f"GitHub event received: {event_type!r}")

    if event_type == "pull_request":
        action = payload.get("action", "")
        if action not in ("opened", "synchronize", "reopened"):
            return {"action": "ignored", "reason": f"PR action {action!r} not reviewed"}

        pr = payload["pull_request"]
        repo = payload["repository"]
        return {
            "action": "review",
            "platform": "github",
            "repo_full_name": repo["full_name"],
            "repo_url": repo["clone_url"],
            "branch": pr["head"]["ref"],
            "base_branch": pr["base"]["ref"],
            "pr_number": pr["number"],
            "commit_sha": pr["head"]["sha"],
            "mode": "INCREMENTAL",
        }

    if event_type == "push":
        ref = payload.get("ref", "")
        if not ref.startswith("refs/heads/"):
            return {"action": "ignored", "reason": "Not a branch push"}
        branch = ref.removeprefix("refs/heads/")
        repo = payload["repository"]
        return {
            "action": "review",
            "platform": "github",
            "repo_full_name": repo["full_name"],
            "repo_url": repo["clone_url"],
            "branch": branch,
            "mode": "INCREMENTAL",
        }

    return {"action": "ignored", "reason": f"Event {event_type!r} not handled"}
