from app.core.router import detect_query_intent
from app.core.tool_router import select_tool
from app.core.tools import deduplicate_results

from app.core.domain_loader import (
    get_domain_tools,
    get_domain_retrieval_rules,
)
from app.core.tools import deduplicate_results
from app.core.router import detect_query_intent
from app.core.tool_router import select_tool



def sort_results(results, route):
    """
    Retrieval sonuçlarını final sıralamaya sokar.

    Domain'e özel boost kuralları aktif domain retrieval_rules modülünden alınır.

    Öncelik:
    1. semantic_rerank_score varsa onu kullan
    2. Yoksa domain boost sonrası final_score kullan
    3. Yoksa ham score kullan
    """
    retrieval_rules = get_domain_retrieval_rules()

    boosted = [
        retrieval_rules.apply_domain_boosts(item, route)
        for item in results
    ]

    return sorted(
        boosted,
        key=lambda x: (
            x.get("semantic_rerank_score")
            if x.get("semantic_rerank_score") is not None
            else x.get("final_score", x.get("score", 0))
        ),
        reverse=True
    )


def run_selected_tool(query: str, route: dict, selected_tool: str, top_k: int):
    """
    Tool router'ın seçtiği tool'u aktif domain tools modülünden çalıştırır.

    Örnek:
    ACTIVE_DOMAIN = "automotive"

    selected_tool = "product_code_tool"
    domain_tools.product_code_tool(...) çalışır.
    """
    domain_tools = get_domain_tools()

    if selected_tool == "product_code_tool":
        return domain_tools.product_code_tool(route, top_k=top_k)

    if selected_tool == "image_search_tool":
        return domain_tools.image_search_tool(route, top_k=top_k)

    if selected_tool == "recommendation_tool":
        return domain_tools.recommendation_tool(route, top_k=top_k)

    if selected_tool == "technical_qa_tool":
        return domain_tools.technical_qa_tool(query, top_k=top_k, route=route)

    return domain_tools.semantic_search_tool(query, top_k=top_k)


def retrieve(query: str, top_k: int = 5):
    """
    Ana retrieval orchestration fonksiyonu.

    Akış:
    1. Query intent tespit edilir
    2. Tool router hangi tool'un çalışacağını seçer
    3. Seçili tool sonuç üretir
    4. Gerekirse strict family filter uygulanır
    5. Gerekirse recommendation score hesaplanır
    6. Sonuçlar sıralanır ve döndürülür
    """
    route = detect_query_intent(query)
    selected_tool = select_tool(query, route)

    results = run_selected_tool(
        query=query,
        route=route,
        selected_tool=selected_tool,
        top_k=top_k
    )

    # Strict family sadece ürün/görsel/öneri tarafında uygulanır.
    retrieval_rules = get_domain_retrieval_rules()

    if selected_tool in ["image_search_tool", "recommendation_tool"]:
        results = retrieval_rules.apply_strict_family_filter(results, route)

    if selected_tool == "recommendation_tool":
        results = retrieval_rules.sort_recommendation_results(
            results=results,
            route=route,
        )

    results = deduplicate_results(results)

    for item in results:
        item["selected_tool"] = selected_tool
        item["intent"] = route.get("intent")
        item["strict_family"] = route.get("strict_family")

    return results[:top_k]


def hybrid_search(query: str, top_k: int = 5):
    """
    Geriye dönük uyumluluk için tutuldu.
    Yeni önerilen isim: retrieve()
    """
    return retrieve(query=query, top_k=top_k)