"""Cross-Encoder reranker using sentence-transformers."""

from loguru import logger

from app.rag.hybrid_search import SearchResult

_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder(_RERANK_MODEL)
            logger.info(f"Loaded Cross-Encoder model: {_RERANK_MODEL}")
        except Exception as exc:
            logger.warning(f"Cross-Encoder not available: {exc}")
    return _reranker


def rerank(query: str, results: list[SearchResult], top_k: int | None = None) -> list[SearchResult]:
    """Rerank search results using Cross-Encoder model.

    Args:
        query: The original search query.
        results: Initial search results from hybrid_search.
        top_k: Max results to return. Defaults to len(results).

    Returns:
        Re-ranked list of SearchResult with updated rrf_score.
    """
    if not results:
        return results

    reranker = _get_reranker()
    if reranker is None:
        logger.warning("Cross-Encoder not available — returning unranked results")
        return results[:top_k] if top_k else results

    try:
        pairs = [(query, r.content) for r in results]
        scores = reranker.predict(pairs)

        for result, score in zip(results, scores):
            result.rrf_score = float(score)  # overwrite with reranker score

        reranked = sorted(results, key=lambda r: r.rrf_score, reverse=True)
        return reranked[:top_k] if top_k else reranked
    except Exception as exc:
        logger.warning(f"Reranking failed: {exc}")
        return results[:top_k] if top_k else results
