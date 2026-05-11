import re

from app.domains.automotive.router_rules import (
    IMAGE_WORDS,
    KNOWN_BRANDS,
    RECOMMENDATION_WORDS,
    PART_KEYWORDS,
    STRICT_FAMILY_RULES,
    STRICT_FAMILY_PRIORITY,
)

PRODUCT_CODE_PATTERN = re.compile(r"\b[A-Z0-9]+(?:-[A-Z0-9]+)+\b")


def detect_strict_family(query: str):
    """
    Sorgunun hangi strict ürün ailesine ait olduğunu bulur.

    Örnek:
    - "akü şarj cihazı görseli" -> battery_charger
    - "akü görseli" -> battery
    - "fren diski" -> brake_disc

    Priority list önemlidir.
    Çünkü "akü şarj cihazı" içinde "akü" de geçer.
    Önce daha spesifik aileler kontrol edilmelidir.
    """
    q = query.lower()

    for family in STRICT_FAMILY_PRIORITY:
        rule = STRICT_FAMILY_RULES.get(family)
        if not rule:
            continue

        for kw in rule["keywords"]:
            if kw in q:
                return family

    return None


def is_recommendation_request(query: str) -> bool:
    q = query.lower()
    return any(word in q for word in RECOMMENDATION_WORDS)


def extract_product_codes(query: str):
    return PRODUCT_CODE_PATTERN.findall(query.upper())


def is_image_request(query: str) -> bool:
    q = query.lower()
    return any(word in q for word in IMAGE_WORDS)


def extract_brand(query: str):
    q = query.upper()

    for brand in KNOWN_BRANDS:
        if brand in q:
            if brand == "PERFORMANCE PLUS":
                return "PERFORMENCE PLUS"
            return brand

    return None


def extract_part_keywords(query: str):
    q = query.lower()
    matched = []

    for _, keywords in PART_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
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


def detect_query_intent(query: str): #query içeriğine göre keywordslerden ayıklıyoruz hangi toollara gideceğini
    product_codes = extract_product_codes(query)
    brand = extract_brand(query)
    part_keywords = extract_part_keywords(query)
    only_images = is_image_request(query)
    query_terms = clean_query_terms(query)
    strict_family = detect_strict_family(query)

    #true dönenler ile ilgili çıktıları üretiyoruz var ise içinde query keyword
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
    }