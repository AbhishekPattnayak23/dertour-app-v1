from ...core.security import get_current_user
from ...db.session import get_db
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
import uuid
from datetime import datetime

router = APIRouter()


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = []
    extra: Optional[Dict[str, Any]] = {}


class DocumentCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Document content")
    metadata: Optional[DocumentMetadata] = None


class DocumentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    metadata: Optional[DocumentMetadata] = None


class DocumentResponse(BaseModel):
    id: str
    content: str
    metadata: Optional[DocumentMetadata] = None
    created_at: datetime
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    top_k: Optional[int] = Field(5, ge=1, le=100, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = {}
    similarity_threshold: Optional[float] = Field(0.0, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: Optional[DocumentMetadata] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    took_ms: Optional[float] = None


# In-memory store for demonstration purposes
_documents_store: Dict[str, DocumentResponse] = {}


def _get_document_or_404(document_id: str) -> DocumentResponse:
    doc = _documents_store.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    return doc


@router.get("/health", summary="Health check for knowledge service")
async def health_check():
    return {"status": "ok", "service": "knowledge", "documents_count": len(_documents_store)}


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=201,
    summary="Create a new document",
)
async def create_document(payload: DocumentCreate):
    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()
    doc = DocumentResponse(
        id=doc_id,
        content=payload.content,
        metadata=payload.metadata or DocumentMetadata(),
        created_at=now,
        updated_at=now,
    )
    _documents_store[doc_id] = doc
    return doc


@router.get(
    "/documents",
    response_model=List[DocumentResponse],
    summary="List all documents",
)
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(20, ge=1, le=200, description="Maximum number of documents to return"),
    tag: Optional[str] = Query(None, description="Filter documents by tag"),
):
    docs = list(_documents_store.values())

    if tag:
        docs = [
            d for d in docs
            if d.metadata and d.metadata.tags and tag in d.metadata.tags
        ]

    docs.sort(key=lambda d: d.created_at, reverse=True)
    return docs[skip: skip + limit]


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Retrieve a document by ID",
)
async def get_document(document_id: str):
    return _get_document_or_404(document_id)


@router.put(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Update an existing document",
)
async def update_document(document_id: str, payload: DocumentUpdate):
    doc = _get_document_or_404(document_id)

    updated_content = payload.content if payload.content is not None else doc.content
    updated_metadata = payload.metadata if payload.metadata is not None else doc.metadata

    updated_doc = DocumentResponse(
        id=doc.id,
        content=updated_content,
        metadata=updated_metadata,
        created_at=doc.created_at,
        updated_at=datetime.utcnow(),
    )
    _documents_store[document_id] = updated_doc
    return updated_doc


@router.delete(
    "/documents/{document_id}",
    status_code=204,
    summary="Delete a document",
)
async def delete_document(document_id: str):
    _get_document_or_404(document_id)
    del _documents_store[document_id]
    return None


@router.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=201,
    summary="Upload a document file",
)
async def upload_document(
    file: UploadFile = File(..., description="Text file to upload"),
    title: Optional[str] = Query(None, description="Optional document title"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
):
    allowed_content_types = {
        "text/plain",
        "text/markdown",
        "application/json",
        "text/csv",
        "text/html",
    }

    if file.content_type and file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {allowed_content_types}",
        )

    raw_bytes = await file.read()
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="File must be UTF-8 encoded text.")

    if not content.strip():
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    metadata = DocumentMetadata(
        title=title or file.filename,
        source=file.filename,
        tags=tag_list,
    )

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()
    doc = DocumentResponse(
        id=doc_id,
        content=content,
        metadata=metadata,
        created_at=now,
        updated_at=now,
    )
    _documents_store[doc_id] = doc
    return doc


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search documents using a query string",
)
async def search_documents(request: SearchRequest):
    import time

    start = time.perf_counter()
    query_lower = request.query.lower()
    results: List[SearchResult] = []

    for doc in _documents_store.values():
        content_lower = doc.content.lower()

        if query_lower in content_lower:
            occurrences = content_lower.count(query_lower)
            score = min(1.0, occurrences * 0.1 + len(query_lower) / max(len(content_lower), 1))
        else:
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = query_words & content_words
            if not overlap:
                continue
            score = len(overlap) / max(len(query_words), 1) * 0.5

        if score < request.similarity_threshold:
            continue

        results.append(
            SearchResult(
                id=doc.id,
                content=doc.content[:500] + ("..." if len(doc.content) > 500 else ""),
                score=round(score, 4),
                metadata=doc.metadata,
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    results = results[: request.top_k]

    elapsed_ms = (time.perf_counter() - start) * 1000

    return SearchResponse(
        query=request.query,
        results=results,
        total=len(results),
        took_ms=round(elapsed_ms, 3),
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search documents via GET query parameter",
)
async def search_documents_get(
    q: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(5, ge=1, le=100, description="Number of results"),
    threshold: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score"),
):
    return await search_documents(
        SearchRequest(query=q, top_k=top_k, similarity_threshold=threshold)
    )


@router.delete(
    "/documents",
    status_code=204,
    summary="Delete all documents (use with caution)",
)
async def delete_all_documents(confirm: bool = Query(False, description="Must be true to confirm deletion")):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Set 'confirm=true' query parameter to delete all documents.",
        )
    _documents_store.clear()
    return None

@router.get("/search", response_model=dict)
async def search_knowledge(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Search knowledge documents."""
    return {"message": "Knowledge search endpoint", "query": query}

@router.get("/documents", response_model=dict)
async def get_documents(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get knowledge documents."""
    return {"message": "Knowledge documents endpoint"}
