from app.core.db import (
    search_items_by_product_code,
    search_items_by_filters,
)
from app.core.search import search_by_text


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


def product_code_tool(route, top_k=5):
    results = []

    for code in route["product_codes"]:
        exact = search_items_by_product_code(code)
        results.extend(exact)

    if results:
        return deduplicate_results(results)[:top_k]

    return []


def image_search_tool(route, top_k=5):
    results = search_items_by_filters(
        query_terms=[],
        only_images=True,
        brand=route["brand"],
        part_keywords=route["part_keywords"],
        limit=top_k * 5,
    )

    for item in results:
        item["match_type"] = "image_metadata_tool"

    return deduplicate_results(results)[:top_k]


def recommendation_tool(route, top_k=5):
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


def semantic_search_tool(query, top_k=5):
    results = search_by_text(query, top_k=top_k)

    for item in results:
        item["match_type"] = "semantic_search_tool"

    return deduplicate_results(results)[:top_k]


def technical_qa_tool(query, top_k=5):
    results = search_by_text(query, top_k=top_k)

    # Teknik sorularda önce text kaynakları öne gelsin.
    text_results = [x for x in results if x.get("item_type") == "text"]
    image_results = [x for x in results if x.get("item_type") == "image"]

    ordered = text_results + image_results

    for item in ordered:
        item["match_type"] = "technical_qa_tool"

    return deduplicate_results(ordered)[:top_k]