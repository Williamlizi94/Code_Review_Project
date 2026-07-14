import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class KnowledgeDocument(Base, UUIDMixin, TimestampMixin):
    """A document in the RAG knowledge base."""

    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # Category: coding_standard | defect_case | review_history | custom
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Original file path in S3 / MinIO
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Status: PENDING | PROCESSING | READY | FAILED
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    user: Mapped["User | None"] = relationship("User", back_populates="knowledge_docs")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeDocument {self.title!r} category={self.category}>"


class KnowledgeChunk(Base, UUIDMixin, TimestampMixin):
    """A chunk of a knowledge document with its vector embedding."""

    __tablename__ = "knowledge_chunks"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Chunk position within document
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Extra metadata: language, function_name, class_name, line_start, line_end
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Vector embedding stored as JSON array (will be pgvector column after migration)
    # The actual vector(1536) column is added in the Alembic migration
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument", back_populates="chunks"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk doc={self.doc_id} idx={self.chunk_index}>"
