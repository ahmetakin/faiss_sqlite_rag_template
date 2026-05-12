"""
Automotive tool routing rules.

Bu dosya otomotiv domain'inde hangi sorgunun hangi retrieval tool'a gideceğini
belirleyen domain özel kuralları tutar.
"""


TECHNICAL_WORDS = [
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


def is_technical_question(query: str) -> bool:
    """
    Sorgunun teknik soru olup olmadığını belirler.

    Örnek:
    - "DPF nasıl temizlenir?"
    - "Fren balatası aşınırsa ne olur?"
    - "Yağ lambası kırmızı yanarsa ne yapılmalı?"
    """
    q = query.lower()
    return any(word in q for word in TECHNICAL_WORDS)


def select_tool_by_domain(query: str, route: dict) -> str | None:
    """
    Automotive domain özel tool seçimi.

    None dönerse core/tool_router default seçime devam eder.
    """
    intent = route.get("intent")

    if intent == "product_code":
        return "product_code_tool"

    if intent == "image_search":
        return "image_search_tool"

    if intent == "recommendation":
        return "recommendation_tool"

    if is_technical_question(query):
        return "technical_qa_tool"

    return None