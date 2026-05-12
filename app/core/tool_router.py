"""
Generic tool router.

Bu dosya hangi retrieval tool'un çalışacağını belirler.
Domain özel kararlar aktif domain'in tool_rules.py dosyasından gelir.
"""

from app.core.domain_loader import get_domain_tool_rules


def select_tool(query: str, route: dict) -> str:
    """
    Kullanıcı sorgusu ve route bilgisine göre çalışacak tool'u seçer.

    Akış:
    1. Aktif domain tool_rules modülünden karar almaya çalışır.
    2. Domain karar verirse onu kullanır.
    3. Domain karar vermezse generic fallback olarak semantic_search_tool döner.
    """
    domain_tool_rules = get_domain_tool_rules()

    selected_tool = domain_tool_rules.select_tool_by_domain(
        query=query,
        route=route,
    )

    if selected_tool:
        return selected_tool

    return "semantic_search_tool"