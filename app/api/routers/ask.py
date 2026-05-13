from fastapi import APIRouter

from app.api.core.exceptions import internal_server_error
from app.api.schemas.ask import AskRequest, AskResponse
from app.api.services.ask_service import run_ask


router = APIRouter(
    prefix="/ask",
    tags=["Ask"],
)


@router.post("", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Retrieval + LLM cevabı üretir.

    Not:
    Bu endpoint için llama.cpp server açık olmalıdır.
    """
    try:
        result = run_ask(
            question=request.question,
            top_k=request.top_k,
        )

        return result

    except Exception as exc:
        raise internal_server_error(exc)