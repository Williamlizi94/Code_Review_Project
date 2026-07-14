"""Stage 3: AST parsing for structural context extraction."""

import os

from loguru import logger

from app.review.pipeline.base import PipelineContext, PipelineStage


class ASTParseStage(PipelineStage):
    name = "ast_parse"

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        """AST parsing is done on-demand by the LangGraph agent via parse_ast tool.

        This stage is a no-op placeholder; the agent calls parse_ast() as needed
        during its ReAct loop in Stage 5.
        """
        logger.info("[Stage 3] AST parsing delegated to LangGraph agent tool calls")
        return ctx
