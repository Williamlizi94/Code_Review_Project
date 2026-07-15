"""Stage 4: RAG retrieval â€” find similar historical defects."""

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.hybrid_search import hybrid_search
from app.rag.rerank import rerank
from app.review.pipeline.base import PipelineContext, PipelineStage


class RAGRetrievalStage(PipelineStage):
    name = "rag_retrieval"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.error:
            return ctx

        # Build query from static issues
        if not ctx.static_issues and not ctx.snippet_content:
            logger.info("[Stage 4] No issues or content for RAG retrieval â€” skipping")
            return ctx

        # Summarize top issues for retrieval query
        issue_summary = "; ".join(
            f"{i.category or 'issue'}: {i.message[:100]}"
            for i in ctx.static_issues[:10]
        )
        query = issue_summary or ctx.snippet_content or ""
        if len(query) > 500:
            query = query[:500]

        logger.info(f"[Stage 4] RAG retrieval for: {query[:80]!r}")
        try:
            results = await hybrid_search(query, self.db, top_k=10, user_id=ctx.user_id)
            ranked = rerank(query, results, top_k=5)

            if ranked:
                rag_blocks = []
                for r in ranked:
                    rag_blocks.append(
                        f"**[Relevance: {r.rrf_score:.3f}]**\n{r.content}"
                    )
                ctx.rag_context = "\n\n---\n\n".join(rag_blocks)
                logger.info(f"[Stage 4] Retrieved {len(ranked)} RAG chunks")
            else:
                ctx.rag_context = None
                logger.info("[Stage 4] No RAG results found")
        except Exception as exc:
            logger.warning(f"[Stage 4] RAG retrieval failed (non-fatal): {exc}")
            ctx.rag_context = None

        return ctx
