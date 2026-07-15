"""Hybrid search: BM25 keyword + pgvector cosine similarity, fused with RRF."""

import uuid
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


_RRF_K = 60


async def hybrid_search(
    query: str,
    db: AsyncSession,
    top_k: int = 5,
    category: str | None = None,
    user_id: uuid.UUID | None = None,
) -> list[SearchResult]:
    """Perform scoped BM25 + vector search and fuse results with RRF."""
    stmt = (
        select(KnowledgeChunk, KnowledgeDocument.category)
        .join(KnowledgeDocument, KnowledgeChunk.doc_id == KnowledgeDocument.id)
        .where(KnowledgeDocument.status == "READY")
    )
    if category:
        stmt = stmt.where(KnowledgeDocument.category == category)
    if user_id:
        stmt = stmt.where(KnowledgeDocument.user_id == user_id)
    stmt = stmt.limit(5000)

    rows = (await db.execute(stmt)).all()
    if not rows:
        return []

    chunks = [row[0] for row in rows]

    corpus = [c.content for c in chunks]
    tokenized = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())

    bm25_ranked = sorted(
        enumerate(bm25_scores), key=lambda x: x[1], reverse=True
    )[: top_k * 3]

    try:
        query_vec = await embed_single(query)
        vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

        filters = ["kd.status = 'READY'", "kc.embedding IS NOT NULL"]
        params: dict[str, object] = {"query_vector": vec_str, "limit": top_k * 3}
        if category:
            filters.append("kd.category = :category")
            params["category"] = category
        if user_id:
            filters.append("kd.user_id = :user_id")
            params["user_id"] = str(user_id)

        where_clause = " AND ".join(filters)
        vector_sql = text(
            f"""
            SELECT kc.id, 1 - (kc.embedding <=> CAST(:query_vector AS vector)) AS score
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kc.doc_id = kd.id
            WHERE {where_clause}
            ORDER BY kc.embedding <=> CAST(:query_vector AS vector)
            LIMIT :limit
            """
        )
        vec_rows = (await db.execute(vector_sql, params)).all()
        vec_id_score = {str(r[0]): float(r[1]) for r in vec_rows}
    except Exception as exc:
        logger.warning(f"Vector search failed, falling back to BM25 only: {exc}")
        vec_id_score = {}

    chunk_map = {str(c.id): c for c in chunks}
    rrf_scores: dict[str, float] = {}

    for rank, (idx, score) in enumerate(bm25_ranked):
        cid = str(chunks[idx].id)
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank + 1)

    vec_ranked = sorted(vec_id_score.items(), key=lambda x: x[1], reverse=True)
    for rank, (cid, score) in enumerate(vec_ranked):
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank + 1)

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
                metadata=chunk.extra_metadata,
                vector_score=vec_id_score.get(cid, 0.0),
                rrf_score=rrf,
            )
        )

    return results
