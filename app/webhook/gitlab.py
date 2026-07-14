"""GitLab webhook handler."""

import json

from fastapi import HTTPException, Request, status
from loguru import logger

from app.config import get_settings

settings = get_settings()


def verify_gitlab_token(request: Request) -> None:
    """Validate GitLab's X-Gitlab-Token header."""
    if not settings.gitlab_webhook_token:
        return
    token = request.headers.get("X-Gitlab-Token", "")
    if token != settings.gitlab_webhook_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GitLab webhook token",
        )


async def handle_gitlab_event(request: Request) -> dict:
    """Parse and handle a GitLab webhook event."""
    verify_gitlab_token(request)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("object_kind", "")
    logger.info(f"GitLab event received: {event_type!r}")

    if event_type == "merge_request":
        attrs = payload.get("object_attributes", {})
        action = attrs.get("action", "")
        if action not in ("open", "update", "reopen"):
            return {"action": "ignored", "reason": f"MR action {action!r} not reviewed"}

        project = payload.get("project", {})
        return {
            "action": "review",
            "platform": "gitlab",
            "project_id": project.get("id"),
            "repo_url": project.get("git_http_url", ""),
            "branch": attrs.get("source_branch", ""),
            "base_branch": attrs.get("target_branch", ""),
            "mr_iid": attrs.get("iid"),
            "commit_sha": attrs.get("last_commit", {}).get("id"),
            "mode": "INCREMENTAL",
        }

    if event_type == "push":
        ref = payload.get("ref", "")
        branch = ref.removeprefix("refs/heads/")
        project = payload.get("project", {})
        return {
            "action": "review",
            "platform": "gitlab",
            "project_id": project.get("id"),
            "repo_url": project.get("git_http_url", ""),
            "branch": branch,
            "mode": "INCREMENTAL",
        }

    return {"action": "ignored", "reason": f"Event {event_type!r} not handled"}
