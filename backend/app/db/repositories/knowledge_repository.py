from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json
import uuid
from sqlalchemy import text, and_, or_, func, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import numpy as np
from app.db.models.knowledge import Document, DocumentChunk, DocumentMetadata, KnowledgeBase
from app.core.exceptions import DatabaseError, NotFoundError
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
    
    def __init__(self, db: Session):
        self.db = db
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
            
        except Exception as e:
            logger.error(f"Error performing vector search: {str(e)}")
            raise DatabaseError(f"Failed to perform vector search: {str(e)}")
    
    def vector_search_with_metadata_filter(
        self,
        knowledge_base_id: str,
        query_embedding: List[float],
        metadata_filters: Dict[str, Any],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[DocumentChunk, float]]:
        """Perform vector search with metadata filtering"""
        try:
            query_vector = np.array(query_embedding)
            
            # Build base query
            query = (
                self.db.query(DocumentChunk)
                .join(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
            )
            
            # Apply metadata filters
            for key, value in metadata_filters.items():
                query = query.filter(
                    DocumentChunk.metadata[key].astext == str(value)
                )
            
            chunks = query.all()
            
            # Calculate similarities
            results = []
            for chunk in chunks:
                if chunk.embedding:
                    chunk_vector = np.array(chunk.embedding)
                    similarity = np.dot(query_vector, chunk_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector)
                    )
                    
                    if similarity >= similarity_threshold:
                        results.append((chunk, float(similarity)))
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error performing filtered vector search: {str(e)}")
            raise DatabaseError(f"Failed to perform filtered vector search: {str(e)}")
    
    def update_chunk_embedding(
        self,
        chunk_id: str,
        embedding: List[float]
    ) -> Optional[DocumentChunk]:
        """Update chunk embedding"""
        try:
            chunk = self.db.query(DocumentChunk).filter(
                DocumentChunk.id == chunk_id
            ).first()
            
            if chunk:
                chunk.embedding = embedding
                self.db.flush()
            
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error updating chunk embedding {chunk_id}: {str(e)}")
            raise DatabaseError(f"Failed to update chunk embedding: {str(e)}")
    
    def delete_document_chunks(self, document_id: str) -> int:

    def list(self, limit: int = 100, offset: int = 0):
        """List knowledge documents with pagination"""
        try:
            return self.db.query(KnowledgeDocument).offset(offset).limit(limit).all()
        except Exception as e:
            raise Exception(f"Error listing knowledge documents: {str(e)}")
        """Delete all chunks for a document"""
        try:
            deleted_count = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete()
            
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Error deleting chunks for document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete document chunks: {str(e)}")
    
    def get_knowledge_base_stats(self, kb_id: str) -> Dict[str, Any]:
        """Get statistics for a knowledge base"""
        try:
            document_count = (
                self.db.query(func.count(Document.id))
                .filter(Document.knowledge_base_id == kb_id)
                .scalar()
            )
            
            chunk_count = (
                self.db.query(func.count(DocumentChunk.id))
                .join(Document)
                .filter(Document.knowledge_base_id == kb_id)
                .scalar()
            )
            
            total_size = (
                self.db.query(func.sum(Document.file_size))
                .filter(Document.knowledge_base_id == kb_id)
                .scalar() or 0
            )
            
            return {
                "document_count": document_count,
                "chunk_count": chunk_count,
                "total_size_bytes": total_size
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting KB stats {kb_id}: {str(e)}")
            raise DatabaseError(f"Failed to get knowledge base stats: {str(e)}")
    
    def create_metadata_index(
        self,
        document_id: str,
        key: str,
        value: str,
        metadata_type: str = "string"
    ) -> DocumentMetadata:
        """Create metadata index entry"""
        try:
            metadata = DocumentMetadata(
                id=str(uuid.uuid4()),
                document_id=document_id,
                key=key,
                value=value,
                metadata_type=metadata_type,
                created_at=datetime.utcnow()
            )
            
            self.db.add(metadata)
            self.db.flush()
            return metadata
        except SQLAlchemyError as e:
            logger.error(f"Error creating metadata index: {str(e)}")
            raise DatabaseError(f"Failed to create metadata index: {str(e)}")
    
    def search_by_metadata(
        self,
        knowledge_base_id: str,
        metadata_filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Search documents by metadata"""
        try:
            query = (
                self.db.query(Document)
                .filter(Document.knowledge_base_id == knowledge_base_id)
            )
            
            for key, value in metadata_filters.items():
                query = query.filter(
                    Document.metadata[key].astext == str(value)
                )
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching by metadata: {str(e)}")
            raise DatabaseError(f"Failed to search by metadata: {str(e)}")