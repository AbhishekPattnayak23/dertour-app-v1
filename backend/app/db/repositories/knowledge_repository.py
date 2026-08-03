"""Knowledge repository for Cosmos DB operations."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from azure.cosmos.aio import ContainerProxy
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentResponse


class KnowledgeRepository:
    """Repository for knowledge document operations in Cosmos DB."""

    def __init__(self, container: ContainerProxy):
        self.container = container

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
