from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from dataclasses import dataclass, field
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class DocumentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class DocumentMetadata:
    document_id: str
    title: str
    filename: str
    file_size: int
    mime_type: str
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "filename": self.filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "extra": self.extra,
        }


class KnowledgeManager:
    """Manages knowledge base documents with CRUD operations."""

    def __init__(self, db_session=None, storage_path: str = "/tmp/knowledge"):
        self.db = db_session
        self.storage_path = storage_path
        self._documents: Dict[str, DocumentMetadata] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_document(
        self,
        title: str,
        filename: str,
        file_size: int,
        mime_type: str,
        tags: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> DocumentMetadata:
        """Create a new document entry in the knowledge base."""
        doc_id = hashlib.sha256(
            f"{title}{filename}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        metadata = DocumentMetadata(
            document_id=doc_id,
            title=title,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            tags=tags or [],
            extra=extra or {},
        )
        self._documents[doc_id] = metadata
        self.logger.info("Created document: %s (%s)", doc_id, title)
        return metadata

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """Retrieve a document by ID."""
        doc = self._documents.get(document_id)
        if self.db is not None:
            try:
                from ....models.knowledge import KnowledgeDocument
                db_doc = self.db.query(KnowledgeDocument).filter(
                    KnowledgeDocument.id == document_id
                ).first()
                if db_doc:
                    return db_doc
            except Exception as exc:
                self.logger.warning("DB query failed, using in-memory: %s", exc)
        return doc

    def list_documents(
        self,
        status: Optional[DocumentStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DocumentMetadata]:
        """List documents with optional filtering."""
        docs = list(self._documents.values())
        if status is not None:
            docs = [d for d in docs if d.status == status]
        if tags:
            docs = [d for d in docs if any(t in d.tags for t in tags)]
        return docs[offset: offset + limit]

    def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[DocumentStatus] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Optional[DocumentMetadata]:
        """Update document metadata."""
        doc = self._documents.get(document_id)
        if doc is None:
            return None
        if title is not None:
            doc.title = title
        if tags is not None:
            doc.tags = tags
        if status is not None:
            doc.status = status
        if extra is not None:
            doc.extra.update(extra)
        doc.updated_at = datetime.utcnow()
        self.logger.info("Updated document: %s", document_id)
        return doc

    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the knowledge base."""
        if document_id not in self._documents:
            return False
        del self._documents[document_id]
        self.logger.info("Deleted document: %s", document_id)
        return True

    def mark_processing(self, document_id: str) -> bool:
        """Mark a document as being processed."""
        return self.update_document(document_id, status=DocumentStatus.PROCESSING) is not None

    def mark_processed(self, document_id: str, extra: Optional[Dict[str, Any]] = None) -> bool:
        """Mark a document as successfully processed."""
        return (
            self.update_document(
                document_id, status=DocumentStatus.PROCESSED, extra=extra
            )
            is not None
        )

    def mark_failed(self, document_id: str, error: Optional[str] = None) -> bool:
        """Mark a document as failed."""
        extra = {"error": error} if error else None
        return (
            self.update_document(document_id, status=DocumentStatus.FAILED, extra=extra)
            is not None
        )

    def archive_document(self, document_id: str) -> bool:
        """Archive a document."""
        return (
            self.update_document(document_id, status=DocumentStatus.ARCHIVED) is not None
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        docs = list(self._documents.values())
        stats: Dict[str, int] = {}
        for status in DocumentStatus:
            stats[status.value] = sum(1 for d in docs if d.status == status)
        return {
            "total_documents": len(docs),
            "by_status": stats,
            "total_size_bytes": sum(d.file_size for d in docs),
        }
