"""Knowledge base management — document ingestion, chunking, and vector storage."""

import json
import uuid
from pathlib import Path

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.rag.embeddings import embed_texts

# ── Chunking ──────────────────────────────────────────────────────────────────

_CHUNK_SIZE = 800   # characters per chunk
_CHUNK_OVERLAP = 150


def _split_by_paragraphs(text: str) -> list[str]:
    """Simple paragraph-based chunking with overlap."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) > _CHUNK_SIZE and current:
            chunks.append(current.strip())
            # Start new chunk with overlap
            words = current.split()
            overlap_words = words[-_CHUNK_OVERLAP // 5:]  # ~30 words overlap
            current = " ".join(overlap_words) + "\n\n" + para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current.strip())
    return chunks


def _split_code_by_functions(content: str, language: str) -> list[str]:
    """Split code at function/class boundaries using Tree-sitter when available."""
    try:
        from tree_sitter_languages import get_parser

        parser = get_parser(language)
        code_bytes = content.encode()
        tree = parser.parse(code_bytes)

        boundaries: list[int] = [0]
        _collect_boundaries(tree.root_node, boundaries, code_bytes)
        boundaries.append(len(code_bytes))
        boundaries = sorted(set(boundaries))

        chunks = []
        for i in range(len(boundaries) - 1):
            chunk = code_bytes[boundaries[i]:boundaries[i + 1]].decode(errors="replace").strip()
            if chunk:
                # Merge small chunks
                if chunks and len(chunks[-1]) + len(chunk) < _CHUNK_SIZE:
                    chunks[-1] += "\n\n" + chunk
                else:
                    chunks.append(chunk)
        return chunks or [content]
    except Exception:
        return _split_by_paragraphs(content)


def _collect_boundaries(node, boundaries: list[int], code_bytes: bytes) -> None:
    func_types = {
        "function_definition", "function_declaration",
        "method_definition", "class_definition", "class_declaration",
    }
    if node.type in func_types:
        boundaries.append(node.start_byte)
    for child in node.children:
        _collect_boundaries(child, boundaries, code_bytes)


# ── Document ingestion ────────────────────────────────────────────────────────

async def ingest_document(
    doc_id: uuid.UUID,
    content: str,
    language: str | None,
    db: AsyncSession,
) -> int:
    """Split document into chunks, embed them, and store in PostgreSQL.

    Returns the number of chunks created.
    """
    # Choose chunking strategy
    if language and language in (
        "python", "javascript", "typescript", "go", "rust", "java"
    ):
        chunks = _split_code_by_functions(content, language)
    else:
        chunks = _split_by_paragraphs(content)

    if not chunks:
        logger.warning(f"No chunks generated for document {doc_id}")
        return 0

    # Batch embedding
    logger.info(f"Embedding {len(chunks)} chunks for document {doc_id}")
    try:
        embeddings = await embed_texts(chunks)
    except Exception as exc:
        logger.error(f"Failed to embed document {doc_id}: {exc}")
        # Mark document as failed
        await db.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.id == doc_id)
            .values(status="FAILED")
        )
        await db.commit()
        return 0

    # Insert chunks with embeddings
    chunk_objs: list[KnowledgeChunk] = []
    for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        chunk = KnowledgeChunk(
            doc_id=doc_id,
            content=chunk_text,
            chunk_index=idx,
            embedding_json=json.dumps(embedding),
            metadata={"language": language, "chunk_index": idx},
        )
        chunk_objs.append(chunk)

    db.add_all(chunk_objs)

    # Update pgvector column using raw SQL after flush
    await db.flush()
    for chunk_obj in chunk_objs:
        embedding = json.loads(chunk_obj.embedding_json)
        vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
        await db.execute(
            f"UPDATE knowledge_chunks SET embedding = '{vec_str}'::vector "  # noqa: S608
            f"WHERE id = '{chunk_obj.id}'"
        )

    # Update document status
    await db.execute(
        update(KnowledgeDocument)
        .where(KnowledgeDocument.id == doc_id)
        .values(status="READY", chunk_count=len(chunk_objs))
    )
    await db.commit()

    logger.info(f"Ingested {len(chunk_objs)} chunks for document {doc_id}")
    return len(chunk_objs)
