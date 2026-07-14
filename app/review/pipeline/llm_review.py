"""Stage 5: LangGraph agent LLM review."""

from loguru import logger

from app.agent.graph import run_review_agent
from app.agent.prompts.review_prompt import build_system_prompt, build_user_prompt
from app.config import get_settings
from app.review.pipeline.base import PipelineContext, PipelineStage

settings = get_settings()


class LLMReviewStage(PipelineStage):
    name = "llm_review"

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.error:
            return ctx

        if not settings.openai_api_key:
            logger.warning("[Stage 5] No OPENAI_API_KEY configured — skipping LLM review")
            return ctx

        # Build diff text for incremental mode
        diff_text = None
        if ctx.mode == "INCREMENTAL" and ctx.workspace_path:
            from app.git.service import get_diff
            diff_text = get_diff(ctx.workspace_path)

        system_prompt = build_system_prompt(
            review_type=ctx.review_type,
            target=ctx.target,
            languages=ctx.languages,
            mode=ctx.mode,
            ruleset_id=ctx.ruleset_id,
            rag_context=ctx.rag_context,
        )
        user_prompt = build_user_prompt(
            code_snippet=ctx.snippet_content,
            snippet_language=ctx.snippet_language,
            workspace_path=ctx.workspace_path,
            diff_text=diff_text,
        )

        logger.info("[Stage 5] Running LangGraph agent review")
        try:
            result = await run_review_agent(system_prompt, user_prompt)
            ctx.llm_issues = result.get("issues", [])
            # Store summary in metadata for report
            ctx.__dict__.setdefault("llm_summary", result.get("summary", ""))
            logger.info(f"[Stage 5] LLM found {len(ctx.llm_issues)} issues")
        except Exception as exc:
            logger.error(f"[Stage 5] LLM review failed: {exc}")
            # Non-fatal — continue with static issues

        return ctx
