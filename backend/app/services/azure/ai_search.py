from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import json
from datetime import datetime

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,

    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    VectorSearchAlgorithmKind,
    SemanticConfiguration,
    SemanticSearch,
    SemanticField,
    SemanticFieldName,

    CorsOptions
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)


class SearchResultType(Enum):
    DOCUMENT = "document"
    CHUNK = "chunk"
    METADATA = "metadata"


@dataclass
class SearchResult:
    id: str
    content: str
    title: Optional[str]
    score: float
    highlights: Optional[Dict[str, List[str]]]
    metadata: Optional[Dict[str, Any]]
    result_type: SearchResultType
    source: Optional[str]
    permissions: Optional[List[str]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class HybridSearchQuery:
    text: str
    vector: Optional[List[float]] = None
    top_k: int = 10
    filters: Optional[str] = None
    select_fields: Optional[List[str]] = None
    highlight_fields: Optional[List[str]] = None
    use_semantic_search: bool = True
    minimum_coverage: float = 0.8
    search_mode: str = "any"
    query_type: str = "semantic"
    permissions: Optional[List[str]] = None


class AzureAISearchService:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str = "documents",
        vector_dimensions: int = 1536
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_name = index_name
        self.vector_dimensions = vector_dimensions

        self.credential = AzureKeyCredential(api_key)
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=self.credential
        )
        self.index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=self.credential
        )

        logger.info(f"Initialized Azure AI Search service for index: {index_name}")

    def create_index(self, delete_if_exists: bool = False) -> bool:
        """Create or update the search index with hybrid search capabilities."""
        try:
            if delete_if_exists:
                try:
                    self.index_client.delete_index(self.index_name)
                    logger.info(f"Deleted existing index: {self.index_name}")
                except ResourceNotFoundError:
                    pass

            # Define vector search configuration
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="default-vector-profile",
                        algorithm_configuration_name="default-hnsw-config"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="default-hnsw-config",
                        kind=VectorSearchAlgorithmKind.HNSW,
                        parameters={
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine"
                        }
                    )
                ]
            )

            # Define semantic search configuration
            semantic_config = SemanticConfiguration(
                name="default-semantic-config",
                prioritized_fields=SemanticField(
                    title_field=SemanticFieldName(field_name="title"),
                    content_fields=[SemanticFieldName(field_name="content")],
                    keywords_fields=[SemanticFieldName(field_name="tags")]
                )
            )

            semantic_search = SemanticSearch(
                configurations=[semantic_config]
            )

            # Define index fields
            fields = [
                SimpleField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True
                ),
                SearchableField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True,
                    analyzer_name="en.microsoft"
                ),
                SearchableField(
                    name="title",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True,
                    sortable=True,
                    analyzer_name="en.microsoft"
                ),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=self.vector_dimensions,
                    vector_search_profile_name="default-vector-profile"
                ),
                SimpleField(
                    name="source",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="result_type",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True,
                    retrievable=True
                ),
                SearchableField(
                    name="tags",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                    searchable=True,
                    filterable=True,
                    facetable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="permissions",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                    filterable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="metadata",
                    type=SearchFieldDataType.String,
                    retrievable=True
                ),
                SimpleField(
                    name="created_at",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="updated_at",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="chunk_id",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="parent_id",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True
                )
            ]

            # Create the index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search,
                cors_options=CorsOptions(allowed_origins=["*"])
            )

            result = self.index_client.create_or_update_index(index)
            logger.info(f"Successfully created/updated index: {result.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index: {str(e)}")
            raise

    def upload_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Upload or update documents in the search index."""
        try:
            # Process documents to ensure proper format
            processed_docs = []
            for doc in documents:
                processed_doc = {
                    "id": doc.get("id"),
                    "content": doc.get("content", ""),
                    "title": doc.get("title", ""),
                    "content_vector": doc.get("content_vector", []),
                    "source": doc.get("source", ""),
                    "result_type": doc.get("result_type", SearchResultType.DOCUMENT.value),
                    "tags": doc.get("tags", []),
                    "permissions": doc.get("permissions", []),
                    "metadata": json.dumps(doc.get("metadata", {})),
                    "created_at": doc.get("created_at", datetime.utcnow().isoformat()),
                    "updated_at": doc.get("updated_at", datetime.utcnow().isoformat()),
                    "chunk_id": doc.get("chunk_id"),
                    "parent_id": doc.get("parent_id"),
                    "@search.action": "upload"
                }
                processed_docs.append(processed_doc)

            result = self.search_client.upload_documents(processed_docs)

            # Check for any failures
            failed_uploads = [r for r in result if not r.succeeded]
            if failed_uploads:
                logger.warning(f"Failed to upload {len(failed_uploads)} documents")
                for failure in failed_uploads:
                    logger.warning(f"Failed upload: {failure.key} - {failure.error_message}")

            success_count = len([r for r in result if r.succeeded])
            logger.info(f"Successfully uploaded {success_count}/{len(documents)} documents")

            return len(failed_uploads) == 0

        except Exception as e:
            logger.error(f"Failed to upload documents: {str(e)}")
            raise

    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from the search index."""
        try:
            documents_to_delete = [{"id": doc_id, "@search.action": "delete"} for doc_id in document_ids]
            result = self.search_client.delete_documents(documents_to_delete)

            failed_deletions = [r for r in result if not r.succeeded]
            if failed_deletions:
                logger.warning(f"Failed to delete {len(failed_deletions)} documents")
                for failure in failed_deletions:
                    logger.warning(f"Failed deletion: {failure.key} - {failure.error_message}")

            success_count = len([r for r in result if r.succeeded])
            logger.info(f"Successfully deleted {success_count}/{len(document_ids)} documents")

            return len(failed_deletions) == 0

        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            raise

    def hybrid_search(self, query: HybridSearchQuery) -> List[SearchResult]:
        """Perform hybrid search combining keyword and vector search."""
        try:
            search_params = {
                "search_text": query.text,
                "top": query.top_k,
                "select": query.select_fields,
                "highlight_fields": query.highlight_fields,
                "search_mode": query.search_mode,
                "minimum_coverage": query.minimum_coverage
            }

            # Add vector search if vector is provided
            if query.vector:
                vector_query = VectorizedQuery(
                    vector=query.vector,
                    k_nearest_neighbors=query.top_k,
                    fields="content_vector"
                )
                search_params["vector_queries"] = [vector_query]

            # Add semantic search configuration
            if query.use_semantic_search:
                search_params["query_type"] = "semantic"
                search_params["semantic_configuration_name"] = "default-semantic-config"

            # Build permission filter
            filter_parts = []
            if query.permissions:
                permission_filter = " or ".join([f"permissions/any(p: p eq '{perm}')" for perm in query.permissions])
                filter_parts.append(f"({permission_filter})")

            # Add additional filters
            if query.filters:
                filter_parts.append(query.filters)

            if filter_parts:
                search_params["filter"] = " and ".join(filter_parts)

            # Execute search
            results = self.search_client.search(**search_params)

            # Convert to SearchResult objects
            search_results = []
            for result in results:
                try:
                    metadata = {}
                    if result.get("metadata"):
                        metadata = json.loads(result["metadata"])
                except (json.JSONDecodeError, TypeError):
                    metadata = {}

                search_result = SearchResult(
                    id=result["id"],
                    content=result.get("content", ""),
                    title=result.get("title"),
                    score=result.get("@search.score", 0.0),
                    highlights=result.get("@search.highlights"),
                    metadata=metadata,
                    result_type=SearchResultType(result.get("result_type", SearchResultType.DOCUMENT.value)),
                    source=result.get("source"),
                    permissions=result.get("permissions", []),
                    created_at=result.get("created_at"),
                    updated_at=result.get("updated_at")
                )
                search_results.append(search_result)

            logger.info(f"Hybrid search returned {len(search_results)} results for query: {query.text[:50]}...")
            return search_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            raise

    def keyword_search(self, query_text: str, filters: Optional[str] = None, top_k: int = 10) -> List[SearchResult]:
        """Perform keyword-only search."""
        query = HybridSearchQuery(
            text=query_text,
            vector=None,
            top_k=top_k,
            filters=filters,
            use_semantic_search=True
        )
        return self.hybrid_search(query)

    def vector_search(self, vector: List[float], filters: Optional[str] = None, top_k: int = 10) -> List[SearchResult]:
        """Perform vector-only search."""
        query = HybridSearchQuery(
            text="*",
            vector=vector,
            top_k=top_k,
            filters=filters,
            use_semantic_search=False
        )
        return self.hybrid_search(query)

    def get_document(self, document_id: str) -> Optional[SearchResult]:
        """Retrieve a specific document by ID."""
        try:
            result = self.search_client.get_document(key=document_id)

            metadata = {}
            if result.get("metadata"):
                try:
                    metadata = json.loads(result["metadata"])
                except (json.JSONDecodeError, TypeError):
                    pass

            return SearchResult(
                id=result["id"],
                content=result.get("content", ""),
                title=result.get("title"),
                score=1.0,
                highlights=None,
                metadata=metadata,
                result_type=SearchResultType(result.get("result_type", SearchResultType.DOCUMENT.value)),
                source=result.get("source"),
                permissions=result.get("permissions", []),
                created_at=result.get("created_at"),
                updated_at=result.get("updated_at")
            )

        except ResourceNotFoundError:
            logger.warning(f"Document not found: {document_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            raise

    def get_index_statistics(self) -> Dict[str, Any]:
        """Get index statistics and information."""
        try:
            index_stats = self.search_client.get_search_index_statistics()
            index_info = self.index_client.get_index(self.index_name)

            return {
                "document_count": index_stats.document_count,
                "storage_size": index_stats.storage_size,
                "vector_index_size": index_stats.vector_index_size if hasattr(index_stats,
                                                                              'vector_index_size') else None,
                "index_name": index_info.name,
                "field_count": len(index_info.fields),
                "vector_dimensions": self.vector_dimensions
            }

        except Exception as e:
            logger.error(f"Failed to get index statistics: {str(e)}")
            raise

    def delete_index(self) -> bool:
        """Delete the search index."""
        try:
            self.index_client.delete_index(self.index_name)
            logger.info(f"Successfully deleted index: {self.index_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Index not found: {self.index_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete index: {str(e)}")
            raise
