from app.core.router import detect_query_intent, STRICT_FAMILY_RULES
from app.core.tool_router import select_tool
from app.core.tools import (
    product_code_tool,
    image_search_tool,
    recommendation_tool,
    semantic_search_tool,
    technical_qa_tool,
    deduplicate_results,
)


def apply_strict_family_filter(results, route):
    strict_family = route.get("strict_family")

    if not strict_family:
        return results

    rule = STRICT_FAMILY_RULES.get(strict_family)
    if not rule:
        return results

    include_prefixes = rule.get("include_product_prefixes", [])
    exclude_prefixes = rule.get("exclude_product_prefixes", [])
    exclude_words = rule.get("exclude_words", [])

    filtered = []

    for item in results:
        product_code = str(item.get("product_code") or "").upper()
        title = str(item.get("title") or "").lower()
        content = str(item.get("content") or "").lower()
        category = str(item.get("category") or "").lower()
        part_group = str(item.get("part_group") or "").lower()

        blob = f"{title} {content} {category} {part_group}"

        if any(product_code.startswith(prefix.upper()) for prefix in exclude_prefixes):
            continue

        if any(word.lower() in blob for word in exclude_words):
            continue

        if include_prefixes:
            matched = any(
                product_code.startswith(prefix.upper())
                for prefix in include_prefixes
            )

            if not matched:
                continue

        filtered.append(item)

    return filtered


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def normalize(value, min_value, max_value):
    value = safe_float(value)

    if max_value <= min_value:
        return 0.0

    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def calculate_recommendation_score(item):
    metadata = item.get("metadata") or {}

    rating = safe_float(metadata.get("rating"))
    review_count = safe_float(metadata.get("review_count"))
    warranty_months = safe_float(metadata.get("warranty_months"))
    cold_cranking_amp = safe_float(metadata.get("cold_cranking_amp"))
    price = safe_float(metadata.get("price"))
    semantic_score = safe_float(item.get("score"))

    rating_score = rating / 5.0 if rating > 0 else 0.0
    review_score = normalize(review_count, 0, 500)
    warranty_score = normalize(warranty_months, 0, 36)
    cca_score = normalize(cold_cranking_amp, 0, 700)

    price_normalized = normalize(price, 0, 5000)
    price_score = 1.0 - price_normalized if price > 0 else 0.0

    recommendation_score = (
        rating_score * 0.35
        + review_score * 0.15
        + warranty_score * 0.20
        + cca_score * 0.15
        + price_score * 0.10
        + semantic_score * 0.05
    )

    item["recommendation_score"] = round(recommendation_score, 4)
    item["rating_score"] = round(rating_score, 4)
    item["review_score"] = round(review_score, 4)
    item["warranty_score"] = round(warranty_score, 4)
    item["cca_score"] = round(cca_score, 4)
    item["price_score"] = round(price_score, 4)
    item["semantic_component"] = round(semantic_score, 4)

    return item


def apply_boosts(item, route):
    score = safe_float(item.get("score"))

    if route.get("only_images") and item.get("item_type") == "image":
        score += 0.35

    if route.get("brand") and item.get("brand"):
        if item["brand"].upper() == route["brand"].upper():
            score += 0.25

    text_blob = " ".join([
        str(item.get("title") or ""),
        str(item.get("category") or ""),
        str(item.get("product_code") or ""),
        str(item.get("content") or ""),
        str(item.get("brand") or ""),
        str(item.get("part_group") or ""),
    ]).lower()

    keyword_hits = 0

    for kw in route.get("part_keywords") or []:
        if kw.lower() in text_blob:
            keyword_hits += 1

    score += keyword_hits * 0.12

    item["final_score"] = round(score, 4)
    return item


def sort_results(results, route):
    """
    Retrieval sonuçlarını final sıralamaya sokar.

    Öncelik:
    1. semantic_rerank_score varsa onu kullan
    2. Yoksa final_score kullan
    3. Yoksa ham FAISS/metadata score kullan
    """
    boosted = [apply_boosts(item, route) for item in results]

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
    route = detect_query_intent(query) #router ile hangi tool'a gidileceğini buluyoruz
    selected_tool = select_tool(query, route) #tool_router içerisinde olan fonksiyon query ile route seçeneklerini yolladık

    results = run_selected_tool( #seçili tooları kullanarak  aramaları yaptırıyoruz iki seçenek var mevcutta tooların kullanabileceği db search ve vector search
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
            calculate_recommendation_score(item) #metadata verisinden önemi hesaplanır öneri istenirse ürünlerin

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
    Yeni isim: retrieve()
    """
    return retrieve(query=query, top_k=top_k)