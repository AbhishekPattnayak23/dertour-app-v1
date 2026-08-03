"""
Search API endpoints with filtering, pagination, and permission validation.
"""
from typing import Optional, List, Any, Dict
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel

try:
    from app.services.search_service import SearchService
except ImportError:
    try:
        from backend.app.services.search_service import SearchService
    except ImportError:
        SearchService = None

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    page: int = 1
    page_size: int = 10
    user_id: Optional[str] = None
    include_citations: bool = False


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    score: float
    citations: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    page: int
    page_size: int
    query: str


def get_search_service() -> SearchService:
    """Dependency injection for SearchService."""
    if SearchService is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service is not available"
        )
    return SearchService()


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Search endpoint with filtering, pagination, and permission validation.
    """
    try:
        # Validate user permissions via search service
        if request.user_id:
            has_permission = await search_service.validate_permissions(
                user_id=request.user_id,
                query=request.query
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to perform this search"
                )

        # Execute search with filtering and ranking
        search_results = await search_service.search(
            query=request.query,
            filters=request.filters,
            page=request.page,
            page_size=request.page_size,
            user_id=request.user_id,
            include_citations=request.include_citations
        )

        return SearchResponse(
            results=search_results.get("results", []),
            total=search_results.get("total", 0),
            page=request.page,
            page_size=request.page_size,
            query=request.query
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_get(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Results per page"),
    user_id: Optional[str] = Query(None, description="User ID for permission validation"),
    filter_type: Optional[str] = Query(None, description="Filter by content type"),
    filter_source: Optional[str] = Query(None, description="Filter by source"),
    include_citations: bool = Query(False, description="Include citation information"),
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    GET search endpoint with query parameters for filtering and pagination.
    """
    try:
        # Build filters from query params
        filters: Dict[str, Any] = {}
        if filter_type:
            filters["type"] = filter_type
        if filter_source:
            filters["source"] = filter_source

        # Validate permissions
        if user_id:
            has_permission = await search_service.validate_permissions(
                user_id=user_id,
                query=q
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to perform this search"
                )

        # Execute search
        search_results = await search_service.search(
            query=q,
            filters=filters if filters else None,
            page=page,
            page_size=page_size,
            user_id=user_id,
            include_citations=include_citations
        )

        return SearchResponse(
            results=search_results.get("results", []),
            total=search_results.get("total", 0),
            page=page,
            page_size=page_size,
            query=q
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/search/{document_id}", status_code=status.HTTP_200_OK)
async def get_search_result(
    document_id: str,
    user_id: Optional[str] = Query(None),
    search_service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """
    Retrieve a specific search result by document ID with citation support.
    """
    try:
        if user_id:
            has_permission = await search_service.validate_permissions(
                user_id=user_id,
                document_id=document_id
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to access this document"
                )

        result = await search_service.get_document(
            document_id=document_id,
            include_citations=True
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )
