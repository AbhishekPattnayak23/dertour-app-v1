"""
Document Indexing Service for Azure AI Search
Handles document indexing, search index management, and knowledge base operations.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IndexingService:
    """
    Service for managing document indexing and search index operations
    using Azure AI Search as the knowledge retrieval backend.
    """

    def __init__(self, search_client=None, index_name: str = "knowledge-index"):
        """
        Initialize the IndexingService.

        Args:
            search_client: Azure AI Search client instance (optional, lazy init)
            index_name: Name of the Azure AI Search index
        """
        self._search_client = search_client
        self.index_name = index_name
        self._index_created = False
        logger.info(f"IndexingService initialized for index: {index_name}")

    # ------------------------------------------------------------------
    # Document Indexing Methods
    # ------------------------------------------------------------------

    def index_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        permissions: Optional[List[str]] = None,
        content_vector: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Index a document with content, metadata, and permission scope.

        Args:
            document_id: Unique identifier for the document
            content: Text content to index
            metadata: Additional metadata fields
            permissions: List of permission scopes for access control
            content_vector: Pre-computed embedding vector for hybrid search

        Returns:
            Dict containing indexing result and document ID
        """
        try:
            # Prepare document for indexing
            doc = {
                "id": document_id,
                "content": content,
                "metadata": metadata or {},
                "permissions": permissions or [],
                "timestamp": self._get_current_timestamp()
            }

            # Add vector field if provided for hybrid search
            if content_vector:
                doc["content_vector"] = content_vector

            # Index the document (mock implementation)
            logger.info(f"Indexing document: {document_id}")

            return {
                "document_id": document_id,
                "status": "indexed",
                "index_name": self.index_name
            }

        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {str(e)}")
            raise

    def bulk_index_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index multiple documents in batch for efficiency.

        Args:
            documents: List of document dictionaries to index

        Returns:
            Dict containing batch indexing results
        """
        try:
            indexed_count = 0
            failed_count = 0

            for doc in documents:
                try:
                    self.index_document(
                        document_id=doc.get("id", str(uuid.uuid4())),
                        content=doc.get("content", ""),
                        metadata=doc.get("metadata"),
                        permissions=doc.get("permissions"),
                        content_vector=doc.get("content_vector")
                    )
                    indexed_count += 1
                except Exception as e:
                    logger.error(f"Failed to index document in batch: {str(e)}")
                    failed_count += 1

            return {
                "total_documents": len(documents),
                "indexed_count": indexed_count,
                "failed_count": failed_count,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Bulk indexing failed: {str(e)}")
            raise

    # ------------------------------------------------------------------
    # Search Index Management Methods
    # ------------------------------------------------------------------

    def create_index(self, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new search index with the specified schema.

        Args:
            schema: Index schema definition (optional, uses default if not provided)

        Returns:
            Dict containing index creation result
        """
        try:
            if not schema:
                schema = self._get_default_index_schema()

            logger.info(f"Creating search index: {self.index_name}")

            # Mock index creation
            self._index_created = True

            return {
                "index_name": self.index_name,
                "status": "created",
                "schema_fields": len(schema.get("fields", []))
            }

        except Exception as e:
            logger.error(f"Failed to create index {self.index_name}: {str(e)}")
            raise

    def delete_index(self) -> Dict[str, Any]:
        """
        Delete the search index and all its documents.

        Returns:
            Dict containing deletion result
        """
        try:
            logger.info(f"Deleting search index: {self.index_name}")

            # Mock index deletion
            self._index_created = False

            return {
                "index_name": self.index_name,
                "status": "deleted"
            }

        except Exception as e:
            logger.error(f"Failed to delete index {self.index_name}: {str(e)}")
            raise

    def update_index_schema(self, schema_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the search index schema with new fields or modifications.

        Args:
            schema_updates: Schema modification definitions

        Returns:
            Dict containing schema update result
        """
        try:
            logger.info(f"Updating schema for index: {self.index_name}")

            return {
                "index_name": self.index_name,
                "status": "schema_updated",
                "updates_applied": len(schema_updates)
            }

        except Exception as e:
            logger.error(f"Failed to update schema for {self.index_name}: {str(e)}")
            raise

    # ------------------------------------------------------------------
    # Private Helper Methods
    # ------------------------------------------------------------------

    def _get_default_index_schema(self) -> Dict[str, Any]:
        """
        Get the default index schema for knowledge documents.

        Returns:
            Dict containing default schema definition
        """
        return {
            "name": self.index_name,
            "fields": [
                {
                    "name": "id",
                    "type": "Edm.String",
                    "key": True,
                    "searchable": False,
                    "filterable": True
                },
                {
                    "name": "content",
                    "type": "Edm.String",
                    "searchable": True,
                    "filterable": False
                },
                {
                    "name": "content_vector",
                    "type": "Collection(Edm.Single)",
                    "searchable": True,
                    "dimensions": 1536,
                    "vector_search_profile": "default"
                },
                {
                    "name": "permissions",
                    "type": "Collection(Edm.String)",
                    "searchable": False,
                    "filterable": True
                },
                {
                    "name": "timestamp",
                    "type": "Edm.DateTimeOffset",
                    "searchable": False,
                    "filterable": True,
                    "sortable": True
                }
            ]
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
