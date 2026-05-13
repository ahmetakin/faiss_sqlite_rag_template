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
from app.core.reranker import rerank_results

from app.core.config import USE_CROSS_ENCODER_RERANKER, CROSS_ENCODER_CANDIDATE_LIMIT
from app.core.cross_encoder_reranker import cross_encoder_rerank_results


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

    # Aynı item_id'ye sahip tekrarları temizliyoruz.
    results = deduplicate_results(results)

    # Metadata alanlarını sonuçlara ekliyoruz.
    # Böylece API, frontend ve eval tarafında hangi tool'un çalıştığını görebiliyoruz.
    for item in results:
        item["selected_tool"] = selected_tool
        item["intent"] = route.get("intent")
        item["strict_family"] = route.get("strict_family")

    # Recommendation sonuçlarında sıralama zaten özel recommendation_mode'a göre yapıldı.
    # Bu yüzden tekrar genel reranker ile bozmak istemiyoruz.
    if selected_tool != "recommendation_tool":
        # Önce hızlı ve hafif rule-based reranker çalışır.
        # Bu sistemin default ve güvenli rerank katmanıdır.
        results = rerank_results(
            query=query,
            results=results,
            top_k=None,
        )

        # Cross encoder opsiyoneldir.
        # Config'te USE_CROSS_ENCODER_RERANKER=True yapılırsa çalışır.
        # Daha yavaştır ama daha hassas sıralama sağlayabilir.
        if USE_CROSS_ENCODER_RERANKER:
            candidate_results = results[:CROSS_ENCODER_CANDIDATE_LIMIT]

            results = cross_encoder_rerank_results(
                query=query,
                results=candidate_results,
                top_k=top_k,
            )

    return results[:top_k]


def hybrid_search(query: str, top_k: int = 5):
    """
    Geriye dönük uyumluluk için tutuldu.
    Yeni önerilen isim: retrieve()
    """
    return retrieve(query=query, top_k=top_k)