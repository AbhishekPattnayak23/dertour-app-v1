from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Title of the knowledge document")
    content: str = Field(..., min_length=1, description="Content of the knowledge document")
    source_url: Optional[str] = Field(None, description="Source URL of the document")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associated with the document")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class KnowledgeDocumentResponse(BaseModel):
    id: str = Field(..., description="Unique identifier of the document")
    title: str = Field(..., description="Title of the knowledge document")
    content: str = Field(..., description="Content of the knowledge document")
    source_url: Optional[str] = Field(None, description="Source URL of the document")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Timestamp when the document was created")
    updated_at: datetime = Field(..., description="Timestamp when the document was last updated")
    embedding_status: str = Field(..., description="Status of document embedding process")

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results to return")
    similarity_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score for results")
    tags: Optional[List[str]] = Field(default_factory=list, description="Filter results by tags")
    include_content: Optional[bool] = Field(True, description="Whether to include full content in results")


class SearchResult(BaseModel):
    id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Document title")
    content: Optional[str] = Field(None, description="Document content (if requested)")
    similarity_score: float = Field(..., description="Similarity score between 0 and 1")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    source_url: Optional[str] = Field(None, description="Source URL of the document")
    created_at: datetime = Field(..., description="Document creation timestamp")


class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(..., description="List of search results")
    total_count: int = Field(..., description="Total number of matching documents")
    query: str = Field(..., description="Original search query")
    execution_time: float = Field(..., description="Search execution time in seconds")