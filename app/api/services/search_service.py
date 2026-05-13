from app.services.retrieval_service import hybrid_search


def run_search(query: str, top_k: int = 5):
    """
    Sadece retrieval çalıştırır.

    LLM cevabı üretmez.
    Debug, test ve frontend kaynak gösterimi için kullanılır.
    """
    return hybrid_search(
        query=query,
        top_k=top_k,
    )