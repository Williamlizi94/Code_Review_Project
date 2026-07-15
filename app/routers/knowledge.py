"""Knowledge base management API endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_user
from app.database import get_db
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.rag.hybrid_search import hybrid_search
from app.rag.rerank import rerank
from app.schemas.knowledge import (
    KnowledgeChunkOut,
    KnowledgeDocumentOut,
    KnowledgeSearchResponse,
    KnowledgeUploadRequest,
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Base"])


@router.post("/upload", response_model=KnowledgeDocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    metadata: KnowledgeUploadRequest,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocumentOut:
    """Upload a knowledge document for RAG indexing."""
    content = await file.read()
    try:
        text_content = content.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not decode file content as text") from exc

    file_ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""
    lang_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "go": "go",
        "rs": "rust",
        "java": "java",
        "rb": "ruby",
    }
    language = lang_map.get(file_ext)

    doc = KnowledgeDocument(
        title=metadata.title,
        category=metadata.category,
        version=metadata.version,
        raw_content=text_content,
        file_path=file.filename,
        file_type=file_ext,
        status="PENDING",
        user_id=current_user.id,
    )
    db.add(doc)
    await db.flush()
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(_ingest_document_bg, str(doc.id), text_content, language)

    return KnowledgeDocumentOut.model_validate(doc)


async def _ingest_document_bg(doc_id: str, content: str, language: str | None) -> None:
    """Background task to chunk and embed the document."""
    from app.database import AsyncSessionLocal
    from app.rag.knowledge import ingest_document

    async with AsyncSessionLocal() as db:
        await ingest_document(uuid.UUID(doc_id), content, language, db)


@router.get("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    q: str = Query(..., min_length=1, description="Search query"),
    category: str | None = Query(None),
    top_k: int = Query(5, ge=1, le=20),
    use_rerank: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeSearchResponse:
    """Hybrid search over knowledge documents visible to the current user."""
    scope_user_id = None if current_user.is_superuser else current_user.id
    results = await hybrid_search(
        q,
        db,
        top_k=top_k * 2,
        category=category,
        user_id=scope_user_id,
    )

    if use_rerank and results:
        results = rerank(q, results, top_k=top_k)
    else:
        results = results[:top_k]

    chunks_out = [
        KnowledgeChunkOut(
            id=uuid.UUID(r.chunk_id),
            doc_id=uuid.UUID(r.doc_id),
            content=r.content,
            chunk_index=r.metadata.get("chunk_index", 0) if r.metadata else 0,
            metadata=r.metadata,
            score=round(r.rrf_score, 4),
        )
        for r in results
    ]

    return KnowledgeSearchResponse(query=q, results=chunks_out, total=len(chunks_out))


@router.get("/documents", response_model=list[KnowledgeDocumentOut])
async def list_documents(
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeDocumentOut]:
    """List knowledge base documents visible to the current user."""
    stmt = select(KnowledgeDocument)
    if not current_user.is_superuser:
        stmt = stmt.where(KnowledgeDocument.user_id == current_user.id)
    if category:
        stmt = stmt.where(KnowledgeDocument.category == category)
    stmt = stmt.order_by(KnowledgeDocument.created_at.desc())

    rows = (await db.execute(stmt)).scalars().all()
    return [KnowledgeDocumentOut.model_validate(r) for r in rows]


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a knowledge document and all its chunks."""
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(doc)
    await db.commit()
