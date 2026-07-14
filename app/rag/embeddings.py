"""OpenAI embedding helper for RAG."""

from loguru import logger
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

settings = get_settings()

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using OpenAI text-embedding-3-small.

    Returns a list of 1536-dimensional float vectors.
    """
    if not texts:
        return []

    client = _get_client()
    # OpenAI recommends replacing newlines with spaces
    cleaned = [t.replace("\n", " ") for t in texts]

    try:
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=cleaned,
        )
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
    except Exception as exc:
        logger.error(f"Embedding error: {exc}")
        raise


async def embed_single(text: str) -> list[float]:
    """Embed a single text and return its vector."""
    results = await embed_texts([text])
    return results[0] if results else []
