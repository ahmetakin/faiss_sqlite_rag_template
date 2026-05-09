from app.core.router import detect_query_intent, STRICT_FAMILY_RULES
from app.core.db import (
    search_items_by_product_code,
    search_items_by_filters
)
from app.core.search import search_by_text


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

        blob = f"{title} {content} {category} {part_group}".lower()

        excluded = False

        for prefix in exclude_prefixes:
            if product_code.startswith(prefix.upper()):
                excluded = True

        for word in exclude_words:
            if word.lower() in blob:
                excluded = True

        if excluded:
            continue

        if include_prefixes:
            matched_prefix = any(
                product_code.startswith(prefix.upper())
                for prefix in include_prefixes
            )

            if not matched_prefix:
                continue

        filtered.append(item)

    return filtered


def deduplicate_results(results):
    seen = set()
    unique = []

    for item in results:
        key = item.get("item_id")
        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique

def get_product_family(code: str):
    parts = code.split("-")
    if len(parts) >= 2:
        return "-".join(parts[:2])
    return code

def filter_only_images(results):
    return [x for x in results if x.get("item_type") == "image"]

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

    # Daha ucuz ürün daha yüksek fiyat skoru alır.
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
    score = float(item.get("score") or 0.0)

    if route["only_images"] and item.get("item_type") == "image":
        score += 0.35 # 0.20 > 0.35

    if route["brand"] and item.get("brand"):
        if item["brand"].upper() == route["brand"].upper():
            score += 0.25

    text_blob = " ".join([
        str(item.get("title") or ""),
        str(item.get("category") or ""),
        str(item.get("product_code") or ""),
        str(item.get("content") or ""),
        str(item.get("brand") or ""),
        str(item.get("part_group") or "")
    ]).lower()

    keyword_hits = 0

    for kw in route["part_keywords"]:
        if kw.lower() in text_blob:
            keyword_hits += 1

    score += keyword_hits * 0.12

    item["final_score"] = round(score, 4)
    return item


def sort_results(results, route):
    boosted = [apply_boosts(x, route) for x in results]
    return sorted(boosted, key=lambda x: x.get("final_score", x.get("score", 0)), reverse=True)


def hybrid_search(query: str, top_k: int = 5):
    route = detect_query_intent(query)
    final_results = []

    # 1) Ürün kodu exact search
    if route["intent"] == "product_code":
        for code in route["product_codes"]:
            exact = search_items_by_product_code(code)
            final_results.extend(exact)

        if final_results:
            final_results = sort_results(deduplicate_results(final_results), route)
            return final_results[:top_k]

        # Exact yoksa aynı ürün ailesinde ara.
        # Örnek: ENGINE-OIL-AKN bulunamazsa ENGINE-OIL-* ailesini getir.
        family_terms = []
        for code in route["product_codes"]:
            family_terms.append(get_product_family(code))

        family_results = search_items_by_filters(
            query_terms=family_terms,
            only_images=False,
            brand=route["brand"],
            part_keywords=route["part_keywords"],
            limit=top_k * 3
        )

        if family_results:
            for item in family_results:
                item["match_type"] = "product_code_family_fallback"

            family_results = sort_results(deduplicate_results(family_results), route)
            return family_results[:top_k]

        return []

    # 2) Görsel isteği: STRICT image filter
    if route["intent"] == "image_search":
        metadata_results = search_items_by_filters(
            query_terms=[],
            only_images=True,
            brand=route["brand"],
            part_keywords=route["part_keywords"],
            limit=top_k * 5
        )


        final_results.extend(metadata_results)
        final_results = deduplicate_results(final_results)
        final_results = apply_strict_family_filter(final_results, route)

        # Eğer net metadata sonucu varsa FAISS fallback'e hiç gitme.
        # Özellikle "BOSCH akü görselini getir" gibi brand + parça sorgularında noise engellenir.
        if final_results and (route["brand"] or route["part_keywords"]):
            final_results = sort_results(final_results, route)
            return final_results[:top_k]

        # Eğer metadata sonucu top_k kadar yeterliyse fallback'e gitme.
        if len(final_results) >= top_k:
            final_results = sort_results(final_results, route)
            return final_results[:top_k]

        # Metadata yetersizse FAISS fallback
        semantic_results = search_by_text(query, top_k=top_k * 3)
        semantic_results = filter_only_images(semantic_results)

        for item in semantic_results:
            item["match_type"] = "semantic_fallback"
            final_results.append(item)

        final_results = deduplicate_results(final_results)
        final_results = apply_strict_family_filter(final_results, route)
        final_results = sort_results(final_results, route)
        return final_results[:top_k]


    # 3) Öneri / karşılaştırma sorgusu
    if route["intent"] == "recommendation":
        metadata_results = search_items_by_filters(
            query_terms=[],
            only_images=True,
            brand=route["brand"],
            part_keywords=route["part_keywords"],
            limit=top_k * 5
        )

        metadata_results = [
            item for item in metadata_results
            if item.get("item_type") == "image"
        ]

        metadata_results = apply_strict_family_filter(metadata_results, route)

        for item in metadata_results:
            item["match_type"] = "recommendation_candidates"
            item["score"] = 0.80
            calculate_recommendation_score(item)

        if metadata_results:
            metadata_results = deduplicate_results(metadata_results)
            metadata_results = sorted(
                metadata_results,
                key=lambda x: x.get("recommendation_score", 0),
                reverse=True
            )
            return metadata_results[:top_k]

        semantic_results = search_by_text(query, top_k=top_k)

        for item in semantic_results:
            item["match_type"] = "semantic_recommendation_fallback"
            calculate_recommendation_score(item)

        semantic_results = deduplicate_results(semantic_results)
        semantic_results = sorted(
            semantic_results,
            key=lambda x: x.get("recommendation_score", 0),
            reverse=True
        )

        return semantic_results[:top_k]

    # 4) Normal semantic search
    semantic_results = search_by_text(query, top_k=top_k)

    for item in semantic_results:
        item["match_type"] = "semantic_faiss"

    final_results = deduplicate_results(semantic_results)
    #final_results = apply_strict_family_filter(final_results, route)
    final_results = sort_results(final_results, route)
    return final_results[:top_k]