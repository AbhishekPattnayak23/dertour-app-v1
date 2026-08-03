"""
Search service with business logic, permission validation, result ranking, and citation support.
"""
import logging
from typing import Optional, List, Any, Dict

logger = logging.getLogger(__name__)


class SearchServiceError(Exception):
    """Base exception for search service errors."""
    pass


class PermissionDeniedError(SearchServiceError):
    """Raised when a user lacks permission for an operation."""
    pass


class SearchService:
    """
    Search business logic service with permission validation,
    result ranking, advanced filtering, and citation support.
    """

    def __init__(self):
        self._initialized = True
        logger.info("SearchService initialized")

    async def validate_permissions(
        self,
        user_id: str,
        query: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> bool:
        """
        Validate that a user has permission to perform a search or access a document.

        Args:
            user_id: The ID of the user requesting access
            query: The search query (optional)
            document_id: The document ID to access (optional)

        Returns:
            True if permitted, False otherwise
        """
        try:
            if not user_id:
                logger.warning("Permission check called with empty user_id")
                return False

            # Permission validation logic
            # In production, this would check against a permission store/ACL
            logger.info(f"Validating permissions for user: {user_id}")

            # Default: allow authenticated users
            return True

        except Exception as e:
            logger.error(f"Permission validation error for user {user_id}: {str(e)}")
            raise SearchServiceError(f"Permission validation failed: {str(e)}") from e

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 10,
        user_id: Optional[str] = None,
        include_citations: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a search with filtering, pagination, and result ranking.

        Args:
            query: Search query string
            filters: Optional dict of filter criteria
            page: Page number (1-indexed)
            page_size: Number of results per page
            user_id: Optional user ID for personalized ranking
            include_citations: Whether to include citation information

        Returns:
            Dict with results, total count, and metadata
        """
        try:
            if not query or not query.strip():
                raise ValueError("Search query cannot be empty")

            if page < 1:
                raise ValueError("Page number must be >= 1")

            if page_size < 1 or page_size > 100:
                raise ValueError("Page size must be between 1 and 100")

            logger.info(f"Executing search: query='{query}', page={page}, page_size={page_size}")

            # Apply advanced filtering
            filtered_results = await self._apply_filters(query, filters)

            # Rank results
            ranked_results = await self._rank_results(filtered_results, query, user_id)

            # Apply pagination
            total = len(ranked_results)
            offset = (page - 1) * page_size
            paginated = ranked_results[offset:offset + page_size]

            # Add citations if requested
            if include_citations:
                paginated = await self._add_citations(paginated)

            return {
                "results": paginated,
                "total": total,
                "page": page,
                "page_size": page_size,
                "query": query
            }

        except ValueError:
            raise
        except SearchServiceError:
            raise
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            raise SearchServiceError(f"Search execution failed: {str(e)}") from e

    async def _apply_filters(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply advanced filtering to search results.

        Args:
            query: Search query
            filters: Filter criteria dict

        Returns:
            Filtered list of results
        """
        try:
            # Base search results (in production, this calls the search backend)
            results = await self._execute_base_search(query)

            if not filters:
                return results

            filtered = []
            for result in results:
                match = True
                for filter_key, filter_value in filters.items():
                    result_metadata = result.get("metadata", {})
                    if filter_key in result_metadata:
                        if result_metadata[filter_key] != filter_value:
                            match = False
                            break
                    elif filter_key in result:
                        if result[filter_key] != filter_value:
                            match = False
                            break
                if match:
                    filtered.append(result)

            logger.debug(f"Filtering reduced results from {len(results)} to {len(filtered)}")
            return filtered

        except Exception as e:
            logger.error(f"Filter application failed: {str(e)}")
            raise SearchServiceError(f"Filtering failed: {str(e)}") from e

    async def _rank_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank search results by relevance score.

        Args:
            results: List of search result dicts
            query: Original search query for relevance scoring
            user_id: Optional user ID for personalized ranking

        Returns:
            Results sorted by relevance score descending
        """
        try:
            if not results:
                return results

            query_terms = set(query.lower().split())

            for result in results:
                base_score = result.get("score", 0.0)

                # Boost score based on query term presence in title
                title = result.get("title", "").lower()
                title_terms = set(title.split())
                title_overlap = len(query_terms & title_terms)

                # Boost score based on query term presence in content
                content = result.get("content", "").lower()
                content_terms = set(content.split())
                content_overlap = len(query_terms & content_terms)

                # Calculate final score with ranking weights
                final_score = (
                    base_score * 0.6 +
                    (title_overlap / max(len(query_terms), 1)) * 0.3 +
                    (content_overlap / max(len(query_terms), 1)) * 0.1
                )
                result["score"] = round(final_score, 4)

            # Sort by score descending
            ranked = sorted(results, key=lambda x: x.get("score", 0.0), reverse=True)
            logger.debug(f"Ranked {len(ranked)} results")
            return ranked

        except Exception as e:
            logger.error(f"Result ranking failed: {str(e)}")
            raise SearchServiceError(f"Ranking failed: {str(e)}") from e

    async def _add_citations(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add citation information to search results.

        Args:
            results: List of search result dicts

        Returns:
            Results with citation data added
        """
        try:
            for result in results:
                if "citations" not in result or result["citations"] is None:
                    result["citations"] = await self._fetch_citations(result.get("id", ""))
            return results

        except Exception as e:
            logger.error(f"Citation retrieval failed: {str(e)}")
            # Citations are supplementary  don't fail the whole search
            logger.warning("Returning results without citations due to error")
            return results

    async def _fetch_citations(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Fetch citations for a specific document.

        Args:
            document_id: Document ID to fetch citations for

        Returns:
            List of citation dicts
        """
        try:
            if not document_id:
                return []
            # In production, fetch from citation store
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch citations for document {document_id}: {str(e)}")
            return []

    async def _execute_base_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute the base search against the search backend.

        Args:
            query: Search query

        Returns:
            Raw search results
        """
        try:
            # In production, this would call Azure Cognitive Search, Elasticsearch, etc.
            # Returns empty list as placeholder  integration with Azure search is handled
            # by the Azure service layer (backend/app/services/azure/)
            logger.debug(f"Base search executed for query: {query}")
            return []
        except Exception as e:
            logger.error(f"Base search execution failed: {str(e)}")
            raise SearchServiceError(f"Search backend error: {str(e)}") from e

    async def get_document(
        self,
        document_id: str,
        include_citations: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID with optional citation support.

        Args:
            document_id: Document ID to retrieve
            include_citations: Whether to include citations

        Returns:
            Document dict or None if not found
        """
        try:
            if not document_id:
                raise ValueError("Document ID cannot be empty")

            logger.info(f"Retrieving document: {document_id}")

            # In production, fetch from document store
            # Returns None as placeholder
            document = None

            if document and include_citations:
                document["citations"] = await self._fetch_citations(document_id)

            return document

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Document retrieval failed for ID {document_id}: {str(e)}")
            raise SearchServiceError(f"Document retrieval failed: {str(e)}") from e
