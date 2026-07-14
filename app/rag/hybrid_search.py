"""Hybrid search: BM25 keyword + pgvector cosine similarity, fused with RRF."""

import json
from dataclasses import dataclass

from loguru import logger
from rank_bm25 import BM25Okapi
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.rag.embeddings import embed_single


@dataclass
class SearchResult:
    chunk_id: str
    doc_id: str
    content: str
    metadata: dict | None
    vector_score: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0


_RRF_K = 60  # Reciprocal Rank Fusion constant


async def hybrid_search(
    query: str,
    db: AsyncSession,
    top_k: int = 5,
    category: str | None = None,
) -> list[SearchResult]:
    """Perform hybrid BM25 + vector search and fuse results with RRF.

    Args:
        query: Natural language or code query string.
        db: Async SQLAlchemy session.
        top_k: Number of results to return.
        category: Optional knowledge document category filter.

    Returns:
        List of SearchResult ranked by RRF score (descending).
    """
    # ── 1. Fetch candidate chunks from DB ────────────────────────────
    stmt = (
        select(KnowledgeChunk, KnowledgeDocument.category)
        .join(KnowledgeDocument, KnowledgeChunk.doc_id == KnowledgeDocument.id)
        .where(KnowledgeDocument.status == "READY")
    )
    if category:
        stmt = stmt.where(KnowledgeDocument.category == category)
    stmt = stmt.limit(5000)  # Cap candidates for BM25

    rows = (await db.execute(stmt)).all()
    if not rows:
        return []

    chunks = [row[0] for row in rows]

    # ── 2. BM25 search ───────────────────────────────────────────────
    corpus = [c.content for c in chunks]
    tokenized = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())

    bm25_ranked = sorted(
        enumerate(bm25_scores), key=lambda x: x[1], reverse=True
    )[:top_k * 3]

    # ── 3. Vector search ─────────────────────────────────────────────
    try:
        query_vec = await embed_single(query)
        vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

        category_filter = ""
        if category:
            category_filter = f"AND kd.category = '{category}'"

        vector_sql = text(
            f"""
            SELECT kc.id, 1 - (kc.embedding <=> '{vec_str}'::vector) AS score
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kc.doc_id = kd.id
            WHERE kd.status = 'READY' {category_filter}
              AND kc.embedding IS NOT NULL
            ORDER BY kc.embedding <=> '{vec_str}'::vector
            LIMIT :limit
            """
        )
        vec_rows = (await db.execute(vector_sql, {"limit": top_k * 3})).all()
        vec_id_score = {str(r[0]): float(r[1]) for r in vec_rows}
    except Exception as exc:
        logger.warning(f"Vector search failed, falling back to BM25 only: {exc}")
        vec_id_score = {}

    # ── 4. RRF fusion ────────────────────────────────────────────────
    chunk_map = {str(c.id): c for c in chunks}
    rrf_scores: dict[str, float] = {}

    # BM25 contribution
    for rank, (idx, score) in enumerate(bm25_ranked):
        cid = str(chunks[idx].id)
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank + 1)

    # Vector contribution
    vec_ranked = sorted(vec_id_score.items(), key=lambda x: x[1], reverse=True)
    for rank, (cid, score) in enumerate(vec_ranked):
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank + 1)

    # Sort by RRF and build result objects
    top_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    results: list[SearchResult] = []
    for cid, rrf in top_ids:
        chunk = chunk_map.get(cid)
        if chunk is None:
            continue
        results.append(
            SearchResult(
                chunk_id=cid,
                doc_id=str(chunk.doc_id),
                content=chunk.content,
                metadata=chunk.metadata,
                vector_score=vec_id_score.get(cid, 0.0),
                rrf_score=rrf,
            )
        )

    return results
