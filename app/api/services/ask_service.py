from app.core.rag import answer_with_rag


def run_ask(question: str, top_k: int = 5):
    """
    Retrieval + LLM cevap üretimi yapar.
    """
    return answer_with_rag(
        question=question,
        top_k=top_k,
    )