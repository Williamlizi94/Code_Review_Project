"""Stage 6: Merge and deduplicate results from static analyzers + LLM."""

from loguru import logger

from app.analyzer.base import AnalyzerIssue, normalize_severity
from app.review.merger import merge_issues
from app.review.pipeline.base import PipelineContext, PipelineStage


class ResultMergeStage(PipelineStage):
    name = "result_merge"

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.error:
            return ctx

        # Convert LLM issues to AnalyzerIssue objects
        llm_analyzer_issues: list[AnalyzerIssue] = []
        for issue in ctx.llm_issues:
            try:
                llm_analyzer_issues.append(
                    AnalyzerIssue(
                        severity=normalize_severity(issue.get("severity", "MEDIUM")),
                        source="llm",
                        message=issue.get("message", ""),
                        file_path=issue.get("file_path"),
                        line_start=issue.get("line_start"),
                        line_end=issue.get("line_end"),
                        rule_id=issue.get("rule_id"),
                        category=issue.get("category"),
                        suggestion=issue.get("suggestion"),
                    )
                )
            except Exception as exc:
                logger.warning(f"[Stage 6] Could not parse LLM issue: {exc}")

        all_issues = ctx.static_issues + llm_analyzer_issues
        ctx.merged_issues = merge_issues(all_issues)
        logger.info(
            f"[Stage 6] Merged: {len(ctx.static_issues)} static + "
            f"{len(llm_analyzer_issues)} LLM → {len(ctx.merged_issues)} unique"
        )
        return ctx
