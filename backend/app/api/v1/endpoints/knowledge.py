from typing import Optional, List
from uuid import UUID

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

from ....core.database import get_db
from ....core.auth import get_current_user

router = APIRouter()


@router.get("/documents", summary="List knowledge documents")
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
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
        return {
            "items": [doc.__dict__ for doc in documents],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/documents", status_code=status.HTTP_201_CREATED, summary="Upload document")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a new document to the knowledge base."""
    try:
        from ....services.knowledge.document_processor import DocumentProcessor
        from ....services.knowledge.knowledge_manager import KnowledgeManager, DocumentStatus

        contents = await file.read()
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

        return {"document_id": doc.document_id, "status": doc.status.value}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/documents/{document_id}", summary="Get document")
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve a specific document by ID."""
    try:
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


@router.put("/documents/{document_id}", summary="Update document")
def update_document(
    document_id: str,
    title: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update document metadata."""
    try:
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


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete document")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a document from the knowledge base."""
    try:
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


@router.get("/documents/{document_id}/content", summary="Get document content")
def get_document_content(
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve the processed content of a document."""
    try:
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
