#router ile elde edilen toolar ile hangi tooları seçeceğimize karar veriyoruz
def select_tool(query: str, route: dict) -> str:
    """
    Deterministic tool router.

    Şimdilik LLM karar vermiyor.
    Kurallarla hangi retrieval tool çalışacak seçiliyor.
    """

    intent = route.get("intent")

    if intent == "product_code":
        return "product_code_tool"

    if intent == "image_search":
        return "image_search_tool"

    if intent == "recommendation":
        return "recommendation_tool"

    q = query.lower()

    technical_words = [
        "neden",
        "ne olur",
        "nasıl",
        "belirti",
        "arıza",
        "yanarsa",
        "koparsa",
        "temizlenir",
        "etkilenir",
        "çalışmaz",
        "devreye girmez",
        "yapılmalı",
    ]

    if any(word in q for word in technical_words):
        return "technical_qa_tool"

    return "semantic_search_tool"