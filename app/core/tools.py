from app.core.db import (
    search_items_by_product_code,
    search_items_by_filters,
    search_technical_by_keywords
)
from app.core.search import search_by_text


def get_product_family(code: str):
    parts = code.split("-")
    if len(parts) >= 2:
        return "-".join(parts[:2])
    return code

def deduplicate_results(results):#dublicate olanları siler
    seen = set()
    unique = []

    for item in results:
        key = item.get("item_id")
        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique


def product_code_tool(route, top_k=5):
    results = []

    # 1) Exact ürün kodu araması
    for code in route["product_codes"]:
        exact = search_items_by_product_code(code)
        results.extend(exact)

    if results:
        return deduplicate_results(results)[:top_k]

    # 2) Exact yoksa ürün ailesi fallback
    family_terms = []

    for code in route["product_codes"]:
        family_terms.append(get_product_family(code))

    family_results = search_items_by_filters(
        query_terms=family_terms,
        only_images=False,
        brand=route["brand"],
        part_keywords=route["part_keywords"],
        limit=top_k * 3,
    )

    for item in family_results:
        item["match_type"] = "product_code_family_fallback"
        item["score"] = 0.95

    return deduplicate_results(family_results)[:top_k]


def image_search_tool(route, top_k=5):
    results = search_items_by_filters(#sqlite dan
        query_terms=[],
        only_images=True,
        brand=route["brand"],
        part_keywords=route["part_keywords"],
        limit=top_k * 5,
    )

    for item in results:
        item["match_type"] = "image_metadata_tool"

    return deduplicate_results(results)[:top_k]


def recommendation_tool(route, top_k=5): #sqlite dan
    results = search_items_by_filters(
        query_terms=[],
        only_images=True,
        brand=route["brand"],
        part_keywords=route["part_keywords"],
        limit=top_k * 5,
    )

    for item in results:
        item["match_type"] = "recommendation_tool"
        item["score"] = 0.80

    return deduplicate_results(results)[:top_k]


def semantic_search_tool(query, top_k=5): #semantic search vektör faiss ile
    results = search_by_text(query, top_k=top_k)

    for item in results:
        item["match_type"] = "semantic_search_tool"

    return deduplicate_results(results)[:top_k]


def technical_qa_tool(query, top_k=5, route=None):
    # 🔥 1️⃣ Önce SQLite keyword search
    keyword_results = search_technical_by_keywords(query, limit=top_k)

    if keyword_results:
        for item in keyword_results:
            item["match_type"] = "technical_keyword_db"
            #item["score"] = 1.0  # keyword match daha güçlü

        return deduplicate_results(keyword_results)[:top_k]

    # 🔥 2️⃣ Fallback → FAISS semantic
    results = search_by_text(query, top_k=top_k * 5)

    q = query.lower()
    strict_family = route.get("strict_family") if route else None
    part_keywords = route.get("part_keywords") if route else []

    def technical_score(item):
        score = float(item.get("score") or 0.0)

        title = str(item.get("title") or "").lower()
        content = str(item.get("content") or "").lower()
        category = str(item.get("category") or "").lower()
        product_code = str(item.get("product_code") or "").upper()
        part_group = str(item.get("part_group") or "").lower()
        item_type = str(item.get("item_type") or "").lower()

        blob = f"{title} {content} {category} {product_code.lower()} {part_group}"

        if item_type == "text":
            score += 0.30

        if category in ["teknik_bilgi", "servis", "bakim", "garanti", "bilgi"]:
            score += 0.20

        if item_type == "image":
            score -= 0.20

        for token in q.split():
            if len(token) >= 4 and token in blob:
                score += 0.05

        for kw in part_keywords or []:
            if kw.lower() in blob:
                score += 0.12

        # strict family logic aynen kalabilir
        if strict_family == "brake_pad":
            if "fren balatası" in blob or product_code.startswith("BRK-PAD"):
                score += 0.60
            if "debriyaj" in blob or product_code.startswith("CLUTCH"):
                score -= 0.80

        item["technical_score"] = round(score, 4)
        item["match_type"] = "technical_qa_tool"
        return item

    scored = [technical_score(item) for item in results]

    scored = sorted(
        scored,
        key=lambda x: x.get("technical_score", x.get("score", 0)),
        reverse=True
    )

    return deduplicate_results(scored)[:top_k]