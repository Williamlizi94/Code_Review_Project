import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    category: str = Field(
        ...,
        description="coding_standard | defect_case | review_history | custom",
    )
    version: str = Field("1.0", max_length=50)


class KnowledgeDocumentOut(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    version: str
    status: str
    chunk_count: int
    file_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    category: str | None = Field(None, description="Filter by category")
    top_k: int = Field(5, ge=1, le=20, description="Number of results")
    use_rerank: bool = Field(True, description="Apply Cross-Encoder reranking")


class KnowledgeChunkOut(BaseModel):
    id: uuid.UUID
    doc_id: uuid.UUID
    content: str
    chunk_index: int
    metadata: dict | None
    score: float | None = None  # relevance score

    model_config = {"from_attributes": True}


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeChunkOut]
    total: int
