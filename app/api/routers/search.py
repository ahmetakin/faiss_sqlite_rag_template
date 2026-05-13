from fastapi import APIRouter

from app.api.core.exceptions import internal_server_error
from app.api.schemas.search import SearchRequest, SearchResponse
from app.api.services.search_service import run_search


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post("", response_model=SearchResponse)
def search(request: SearchRequest):
    """
    Sadece retrieval çalıştırır.

    Örnek:
    - semantic search
    - image search
    - product code search
    - recommendation search
    """
    try:
        sources = run_search(
            query=request.query,
            top_k=request.top_k,
        )

        return {
            "query": request.query,
            "sources": sources,
        }

    except Exception as exc:
        raise internal_server_error(exc)