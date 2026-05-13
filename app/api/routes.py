from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    AskRequest,
    AskResponse,
    SearchRequest,
    SearchResponse,
    HealthResponse,
)
from app.core.rag import answer_with_rag
from app.services.retrieval_service import hybrid_search


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    """
    Servisin ayakta olup olmadığını kontrol eder.
    """
    return {
        "status": "ok",
        "service": "faiss-sqlite-rag-template",
    }


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """
    Sadece retrieval çalıştırır.
    LLM cevabı üretmez.

    Debug, test ve frontend kaynak gösterimi için kullanılır.
    """
    try:
        sources = hybrid_search(
            query=request.query,
            top_k=request.top_k,
        )

        return {
            "query": request.query,
            "sources": sources,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Retrieval + LLM cevap üretimi yapar.
    """
    try:
        result = answer_with_rag(
            question=request.question,
            top_k=request.top_k,
        )

        return result

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))