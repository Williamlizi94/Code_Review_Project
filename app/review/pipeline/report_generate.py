"""Stage 7: Generate review reports (HTML and Markdown)."""

from loguru import logger

from app.report.html import generate_html_report
from app.report.markdown import generate_markdown_report
from app.review.pipeline.base import PipelineContext, PipelineStage


class ReportGenerateStage(PipelineStage):
    name = "report_generate"

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.error:
            return ctx

        llm_summary = getattr(ctx, "llm_summary", "")
        logger.info("[Stage 7] Generating review reports")

        try:
            ctx.report_html = generate_html_report(
                review_id=str(ctx.review_id),
                issues=ctx.merged_issues,
                summary=llm_summary,
                target=ctx.target,
                mode=ctx.mode,
            )
        except Exception as exc:
            logger.warning(f"[Stage 7] HTML report generation failed: {exc}")

        try:
            ctx.report_markdown = generate_markdown_report(
                review_id=str(ctx.review_id),
                issues=ctx.merged_issues,
                summary=llm_summary,
                target=ctx.target,
            )
        except Exception as exc:
            logger.warning(f"[Stage 7] Markdown report generation failed: {exc}")

        return ctx
