from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
from uuid import UUID, uuid4
from sqlalchemy import text, and_, or_, func, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import numpy as np
from azure.cosmos.aio import ContainerProxy
from app.db.models.knowledge import Document, DocumentChunk, DocumentMetadata, KnowledgeBase
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentResponse
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentRepository:
    """Repository for document-related database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_document(
        self,
        knowledge_base_id: str,
        title: str,
        content: str,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a new document"""
        try:
            document = Document(
                id=str(uuid.uuid4()),
                knowledge_base_id=knowledge_base_id,
                title=title,
                content=content,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(document)
            self.db.flush()
            return document
        except SQLAlchemyError as e:
            logger.error(f"Error creating document: {str(e)}")
            raise DatabaseError(f"Failed to create document: {str(e)}")

    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        try:
            return self.db.query(Document).filter(Document.id == document_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve document: {str(e)}")

    def get_documents_by_knowledge_base(
        self,
        knowledge_base_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Get documents by knowledge base ID"""
        try:
            return (
                self.db.query(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving documents for KB {knowledge_base_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve documents: {str(e)}")

    def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Document]:
        """Update document"""
        try:
            document = self.get_document_by_id(document_id)
            if not document:
                return None

            if title is not None:
                document.title = title
            if content is not None:
                document.content = content
            if metadata is not None:
                document.metadata = metadata

            document.updated_at = datetime.utcnow()
            self.db.flush()
            return document
        except SQLAlchemyError as e:
            logger.error(f"Error updating document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to update document: {str(e)}")

    def delete_document(self, document_id: str) -> bool:
        """Delete document and its chunks"""
        try:
            # Delete chunks first
            self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete()

            # Delete document
            deleted_count = self.db.query(Document).filter(
                Document.id == document_id
            ).delete()

            return deleted_count > 0
        except SQLAlchemyError as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete document: {str(e)}")

    def search_documents(
        self,
        knowledge_base_id: str,
        query: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Document]:
        """Search documents by text"""
        try:
            return (
                self.db.query(Document)
                .filter(
                    and_(
                        Document.knowledge_base_id == knowledge_base_id,
                        or_(
                            Document.title.ilike(f"%{query}%"),
                            Document.content.ilike(f"%{query}%")
                        )
                    )
                )
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise DatabaseError(f"Failed to search documents: {str(e)}")


class KnowledgeRepository:
    """Repository for knowledge base and vector search operations"""

    def __init__(self, db: Session = None, container: ContainerProxy = None):
        self.db = db
        self.container = container
        if db:
            self.document_repo = DocumentRepository(db)

    def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> KnowledgeBase:
        """Create a new knowledge base"""
        try:
            kb = KnowledgeBase(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(kb)
            self.db.flush()
            return kb
        except SQLAlchemyError as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            raise DatabaseError(f"Failed to create knowledge base: {str(e)}")

    def get_knowledge_base_by_id(self, kb_id: str) -> Optional[KnowledgeBase]:
        """Get knowledge base by ID"""
        try:
            return self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving knowledge base {kb_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve knowledge base: {str(e)}")

    def get_knowledge_bases_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[KnowledgeBase]:
        """Get knowledge bases by user ID"""
        try:
            return (
                self.db.query(KnowledgeBase)
                .filter(KnowledgeBase.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving knowledge bases for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve knowledge bases: {str(e)}")

    def create_document_chunk(
        self,
        document_id: str,
        content: str,
        embedding: List[float],
        chunk_index: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentChunk:
        """Create a document chunk with embedding"""
        try:
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                content=content,
                embedding=embedding,
                chunk_index=chunk_index,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )

            self.db.add(chunk)
            self.db.flush()
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error creating document chunk: {str(e)}")
            raise DatabaseError(f"Failed to create document chunk: {str(e)}")

    def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        try:
            return (
                self.db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving chunks for document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve document chunks: {str(e)}")

    def vector_search(
        self,
        knowledge_base_id: str,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[DocumentChunk, float]]:
        """Perform vector similarity search"""
        try:
            # Convert query embedding to numpy array for calculation
            query_vector = np.array(query_embedding)

            # Get all chunks for the knowledge base
            chunks = (
                self.db.query(DocumentChunk)
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
                .all()
            )

            # Calculate similarities
            results = []
            for chunk in chunks:
                if chunk.embedding:
                    chunk_vector = np.array(chunk.embedding)
                    # Calculate cosine similarity
                    similarity = np.dot(query_vector, chunk_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector)
                    )

                    if similarity >= similarity_threshold:
                        results.append((chunk, float(similarity)))

            # Sort by similarity (highest first) and limit results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]

        except SQLAlchemyError as e:
            logger.error(f"Error performing vector search: {str(e)}")
            raise DatabaseError(f"Failed to perform vector search: {str(e)}")

    async def create_document(self, document: KnowledgeDocumentCreate) -> KnowledgeDocumentResponse:
        """Create new knowledge document."""
        doc_item = {
            "id": str(uuid4()),
            "title": document.title,
            "content": document.content,
            "category": document.category,
            "tags": document.tags or [],
            "embedding": document.embedding or [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        created_item = await self.container.create_item(doc_item)
        return KnowledgeDocumentResponse(**created_item)

    async def get_document_by_id(self, doc_id: str) -> Optional[KnowledgeDocumentResponse]:
        """Get document by ID."""
        try:
            item = await self.container.read_item(item=doc_id, partition_key=doc_id)
            return KnowledgeDocumentResponse(**item)
        except Exception:
            return None

    async def search_documents(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[KnowledgeDocumentResponse]:
        """Search documents by query."""
        sql_query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.content), LOWER(@query)) OR CONTAINS(LOWER(c.title), LOWER(@query))"
        parameters = [{"name": "@query", "value": query}]

        if category:
            sql_query += " AND c.category = @category"
            parameters.append({"name": "@category", "value": category})

        sql_query += " ORDER BY c.created_at DESC"

        items = []
        async for item in self.container.query_items(
            query=sql_query,
            parameters=parameters,
            max_item_count=limit
        ):
            items.append(KnowledgeDocumentResponse(**item))

        return items
