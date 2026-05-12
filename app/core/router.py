import re

from app.core.domain_loader import get_domain_router_rules

PRODUCT_CODE_PATTERN = re.compile(r"\b[A-Z0-9]+(?:-[A-Z0-9]+)+\b")

def get_router_rules():
    """
    Aktif domain router_rules modülünü döndürür.

    Örnek:
    ACTIVE_DOMAIN = "automotive"
    -> app.domains.automotive.router_rules
    """
    return get_domain_router_rules()

def detect_strict_family(query: str):
    """
    Sorgunun hangi strict ürün ailesine ait olduğunu bulur.

    Kurallar aktif domain'den gelir.
    """
    rules = get_router_rules()

    q = query.lower()

    for family in rules.STRICT_FAMILY_PRIORITY:
        rule = rules.STRICT_FAMILY_RULES.get(family)

        if not rule:
            continue

        for kw in rule["keywords"]:
            if rules.keyword_matches_query(q, kw):
                return family

    return None


def is_recommendation_request(query: str) -> bool:
    rules = get_router_rules()

    q = query.lower()
    return any(word in q for word in rules.RECOMMENDATION_WORDS)


def extract_product_codes(query: str):
    return PRODUCT_CODE_PATTERN.findall(query.upper())


def is_image_request(query: str) -> bool:
    rules = get_router_rules()

    q = query.lower()
    return any(word in q for word in rules.IMAGE_WORDS)


def extract_brand(query: str):
    rules = get_router_rules()

    q = query.upper()

    for brand in rules.KNOWN_BRANDS:
        if brand in q:
            if brand == "PERFORMANCE PLUS":
                return "PERFORMENCE PLUS"
            return brand

    return None


def extract_part_keywords(query: str):
    rules = get_router_rules()

    q = query.lower()
    matched = []

    for _, keywords in rules.PART_KEYWORDS.items():
        for kw in keywords:
            if rules.keyword_matches_query(q, kw):
                matched.extend(keywords)
                break

    return list(set(matched))


def clean_query_terms(query: str):
    q = query.lower()

    remove_words = [
        "görselini", "görsel", "resmini", "resim",
        "fotoğrafını", "fotoğraf", "foto",
        "getir", "göster", "bul", "ürün", "kodlu", "parça",
        "hangisi", "nedir", "nelerdir"
    ]

    for word in remove_words:
        q = q.replace(word, " ")

    terms = [x.strip() for x in q.split() if len(x.strip()) >= 2]
    return terms


def detect_query_intent(query: str):
    """
    Kullanıcı sorgusundan retrieval route bilgisini çıkarır.
    """
    rules = get_router_rules()

    product_codes = extract_product_codes(query)
    brand = extract_brand(query)
    part_keywords = extract_part_keywords(query)
    only_images = is_image_request(query)
    query_terms = clean_query_terms(query)
    strict_family = detect_strict_family(query)

    recommendation_mode = None

    if is_recommendation_request(query):
        recommendation_mode = rules.detect_recommendation_mode(query)

    if product_codes:
        intent = "product_code"
    elif is_recommendation_request(query):
        intent = "recommendation"
    elif only_images:
        intent = "image_search"
    else:
        intent = "semantic_search"

    return {
        "intent": intent,
        "product_codes": product_codes,
        "only_images": only_images,
        "brand": brand,
        "part_keywords": part_keywords,
        "query_terms": query_terms,
        "strict_family": strict_family,
        "recommendation_mode": recommendation_mode,
    }