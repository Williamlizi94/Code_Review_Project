"""Embedding helpers for RAG."""

import asyncio

from loguru import logger
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

settings = get_settings()

_openai_client: AsyncOpenAI | None = None
_ollama_client: AsyncOpenAI | None = None
_local_model = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")
        if settings.openai_base_url:
            _openai_client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        else:
            _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _get_ollama_client() -> AsyncOpenAI:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = AsyncOpenAI(
            api_key="ollama",
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
        )
    return _ollama_client


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(settings.local_embedding_model)
    return _local_model


def _normalize_vectors(vectors) -> list[list[float]]:
    normalized: list[list[float]] = []
    for vector in vectors:
        if hasattr(vector, "tolist"):
            vector = vector.tolist()
        normalized.append([float(value) for value in vector])
    return normalized


def _embed_local(cleaned: list[str]) -> list[list[float]]:
    model = _get_local_model()
    vectors = model.encode(
        cleaned,
        normalize_embeddings=True,
        convert_to_numpy=False,
    )
    return _normalize_vectors(vectors)


async def _embed_with_openai(cleaned: list[str]) -> list[list[float]]:
    response = await _get_openai_client().embeddings.create(
        model=settings.openai_embedding_model,
        input=cleaned,
    )
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


async def _embed_with_ollama(cleaned: list[str]) -> list[list[float]]:
    response = await _get_ollama_client().embeddings.create(
        model=settings.ollama_embedding_model,
        input=cleaned,
    )
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the configured embedding provider."""
    if not texts:
        return []

    cleaned = [t.replace("\n", " ") for t in texts]

    try:
        if settings.embedding_provider == "local":
            return await asyncio.to_thread(_embed_local, cleaned)
        if settings.embedding_provider == "ollama":
            return await _embed_with_ollama(cleaned)
        if settings.embedding_provider == "openai":
            return await _embed_with_openai(cleaned)
        raise RuntimeError("Embedding provider is disabled")
    except Exception as exc:
        logger.error(f"Embedding error: {exc}")
        raise


async def embed_single(text: str) -> list[float]:
    """Embed a single text and return its vector."""
    results = await embed_texts([text])
    return results[0] if results else []
