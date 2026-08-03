from typing import Optional, List, Any, Dict
from uuid import UUID
import uuid
from datetime import datetime
import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    File,
    UploadFile,
    status,
    Query,
)
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....core.database import get_db
from ....core.auth import get_current_user

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


@router.get("/documents", summary="List knowledge documents")
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(20, ge=1, le=200, description="Maximum number of documents to return"),
    tag: Optional[str] = Query(None, description="Filter documents by tag"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all knowledge base documents with pagination."""
    try:
        from ....models.knowledge import KnowledgeDocument
        query = db.query(KnowledgeDocument)
        if status:
            query = query.filter(KnowledgeDocument.status == status)
        total = query.count()
        offset = (page - 1) * page_size
        documents = query.offset(offset).limit(page_size).all()
        
        # Also handle in-memory documents
        docs = list(_documents_store.values())
        if tag:
            docs = [
                d for d in docs
                if d.metadata and d.metadata.tags and tag in d.metadata.tags
            ]
        docs.sort(key=lambda d: d.created_at, reverse=True)
        memory_docs = docs[skip: skip + limit]
        
        return {
            "items": [doc.__dict__ for doc in documents] + [doc.dict() for doc in memory_docs],
            "total": total + len(memory_docs),
            "page": page,
            "page_size": page_size,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create/Upload document"
)
async def upload_document(
    payload: Optional[DocumentCreate] = None,
    file: Optional[UploadFile] = File(None),
    title: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a new document to the knowledge base or create from payload."""
    try:
        if file:
            # Handle file upload
            from ....services.knowledge.document_processor import DocumentProcessor
            from ....services.knowledge.knowledge_manager import KnowledgeManager, DocumentStatus

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

            contents = await file.read()
            
            try:
                content = contents.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=422, detail="File must be UTF-8 encoded text.")

            if not content.strip():
                raise HTTPException(status_code=422, detail="Uploaded file is empty.")

            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

            processor = DocumentProcessor()
            result = processor.process_bytes(
                contents,
                file.filename or "unknown",
                file.content_type,
            )

            manager = KnowledgeManager(db_session=db)
            doc = manager.create_document(
                title=title or file.filename or "Untitled",
                filename=file.filename or "unknown",
                file_size=len(contents),
                mime_type=file.content_type or "application/octet-stream",
            )

            if result.success:
                manager.mark_processed(doc.document_id, extra={"word_count": result.word_count})
            else:
                manager.mark_failed(doc.document_id, error=result.error)

            # Also create in memory store
            metadata = DocumentMetadata(
                title=title or file.filename,
                source=file.filename,
                tags=tag_list,
            )

            doc_id = str(uuid.uuid4())
            now = datetime.utcnow()
            memory_doc = DocumentResponse(
                id=doc_id,
                content=content,
                metadata=metadata,
                created_at=now,
                updated_at=now,
            )
            _documents_store[doc_id] = memory_doc

            return memory_doc

        elif payload:
            # Handle JSON payload
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
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file or JSON payload must be provided"
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=201,
    summary="Upload a document file",
)
async def upload_document_file(
    file: UploadFile = File(..., description="Text file to upload"),
    title: Optional[str] = Query(None, description="Optional document title"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
):
    return await upload_document(file=file, title=title, tags=tags)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get document"
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve a specific document by ID."""
    try:
        # Try memory store first
        memory_doc = _documents_store.get(document_id)
        if memory_doc:
            return memory_doc

        # Try database
        from ....models.knowledge import KnowledgeDocument
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return doc.__dict__
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.put(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Update document"
)
def update_document(
    document_id: str,
    payload: Optional[DocumentUpdate] = None,
    title: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update document metadata."""
    try:
        # Try memory store first
        memory_doc = _documents_store.get(document_id)
        if memory_doc:
            if payload:
                updated_content = payload.content if payload.content is not None else memory_doc.content
                updated_metadata = payload.metadata if payload.metadata is not None else memory_doc.metadata
            else:
                updated_content = memory_doc.content
                updated_metadata = memory_doc.metadata
                if title is not None and updated_metadata:
                    updated_metadata.title = title

            updated_doc = DocumentResponse(
                id=memory_doc.id,
                content=updated_content,
                metadata=updated_metadata,
                created_at=memory_doc.created_at,
                updated_at=datetime.utcnow(),
            )
            _documents_store[document_id] = updated_doc
            return updated_doc

        # Try database
        from ....models.knowledge import KnowledgeDocument
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if title is not None:
            doc.title = title
        db.commit()
        db.refresh(doc)
        return doc.__dict__
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document"
)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a document from the knowledge base."""
    try:
        # Try memory store first
        if document_id in _documents_store:
            del _documents_store[document_id]
            return

        # Try database
        from ....models.knowledge import KnowledgeDocument
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        db.delete(doc)
        db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
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


@router.get("/documents/{document_id}/content", summary="Get document content")
def get_document_content(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve the processed content of a document."""
    try:
        # Try memory store first
        memory_doc = _documents_store.get(document_id)
        if memory_doc:
            return {"document_id": document_id, "content": memory_doc.content}

        # Try database
        from ....models.knowledge import KnowledgeDocument
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return {"document_id": document_id, "content": getattr(doc, "content", None)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/documents/{document_id}/reprocess", summary="Reprocess document")
def reprocess_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger reprocessing of an existing document."""
    try:
        # Check memory store first
        memory_doc = _documents_store.get(document_id)
        if memory_doc:
            return {"document_id": document_id, "status": "reprocessing_queued"}

        # Check database
        from ....models.knowledge import KnowledgeDocument
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == document_id
        ).first()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return {"document_id": document_id, "status": "reprocessing_queued"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search documents using a query string",
)
async def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
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
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await search_documents(
        SearchRequest(query=q, top_k=top_k, similarity_threshold=threshold),
        db=db,
        current_user=current_user
    )
