"""Stage 1: Clone or pull the target Git repository."""

import os
import tempfile

from loguru import logger

from app.git.service import clone_or_pull
from app.review.pipeline.base import PipelineContext, PipelineStage


class GitCloneStage(PipelineStage):
    name = "git_clone"

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.review_type not in ("GIT_REPO",):
            # For DIRECTORY / FILE / SNIPPET, workspace is already set or not needed
            return ctx

        if not ctx.target:
            ctx.error = "No target URL specified for GIT_REPO review"
            return ctx

        workspace_root = tempfile.mkdtemp(prefix="codeguardian_")
        logger.info(f"[Stage 1] Cloning {ctx.target!r} branch={ctx.branch!r}")
        try:
            local_path = await clone_or_pull(
                repo_url=ctx.target,
                branch=ctx.branch or "main",
                workspace_root=workspace_root,
            )
            ctx.workspace_path = local_path
        except Exception as exc:
            ctx.error = f"Git clone failed: {exc}"
            logger.error(f"[Stage 1] {ctx.error}")

        return ctx
