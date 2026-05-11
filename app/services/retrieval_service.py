from app.core.router import detect_query_intent
from app.core.tool_router import select_tool
from app.core.tools import (
    product_code_tool,
    image_search_tool,
    recommendation_tool,
    semantic_search_tool,
    technical_qa_tool,
    deduplicate_results,
)
from app.domains.automotive.retrieval_rules import (
    apply_strict_family_filter,
    calculate_recommendation_score,
    apply_domain_boosts,
)



def sort_results(results, route):
    """
    Retrieval sonuçlarını final sıralamaya sokar.

    Öncelik:
    1. semantic_rerank_score varsa onu kullan
    2. Yoksa domain boost sonrası final_score kullan
    3. Yoksa ham score kullan
    """
    boosted = [apply_domain_boosts(item, route) for item in results]

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
    Tool router'ın seçtiği tool'u çalıştırır.
    """
    if selected_tool == "product_code_tool":
        return product_code_tool(route, top_k=top_k)

    if selected_tool == "image_search_tool":
        return image_search_tool(route, top_k=top_k)

    if selected_tool == "recommendation_tool":
        return recommendation_tool(route, top_k=top_k)

    if selected_tool == "technical_qa_tool":
        return technical_qa_tool(query, top_k=top_k, route=route)

    return semantic_search_tool(query, top_k=top_k)


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
    if selected_tool in ["image_search_tool", "recommendation_tool"]:
        results = apply_strict_family_filter(results, route)

    if selected_tool == "recommendation_tool":
        for item in results:
            calculate_recommendation_score(item)

        results = sorted(
            results,
            key=lambda x: x.get("recommendation_score", 0),
            reverse=True
        )
    else:
        results = sort_results(results, route)

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