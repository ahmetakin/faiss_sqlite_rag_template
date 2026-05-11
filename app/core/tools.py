from app.core.db import (
    search_items_by_product_code,
    search_items_by_filters,
    search_technical_by_keywords
)
from app.core.search import search_by_text

from app.domains.automotive.rules import (
    expand_tokens,
    apply_automotive_semantic_rules,
)

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


def tokenize_query(query: str):
    """
    Kullanıcı sorgusunu anlamlı kelimelere böler.

    Amaç:
    - "kaç", "ne", "mı" gibi zayıf kelimeleri atmak
    - semantic sonuçları daha doğru sıralamak için keyword sinyali üretmek
    """
    stopwords = {
        "ne", "nedir", "nasıl", "neden", "kaç", "mi", "mı", "mu", "mü",
        "ve", "veya", "bir", "bu", "şu", "için", "ile", "gibi",
        "var", "mı", "kapsamında", "kapsamı", "şartları", "nelerdir"
    }

    clean = (
        query.lower()
        .replace("?", " ")
        .replace(",", " ")
        .replace(".", " ")
        .replace(":", " ")
        .replace("-", " ")
    )

    tokens = [
        token.strip()
        for token in clean.split()
        if len(token.strip()) >= 3 and token.strip() not in stopwords
    ]

    return tokens


def apply_semantic_rerank(results, query: str):
    """
    FAISS'ten gelen semantic sonuçları yeniden skorlar.

    Neden gerekli?
    - FAISS benzerlik skoru bazen çok yakın sonuçlar üretir.
    - Örneğin "motor garantisi" sorusunda şanzıman garantisi de yakın gelebilir.
    - Burada title/content/product_code/metadata eşleşmelerine ek puan veriyoruz.

    Bu yöntem:
    - FAISS skorunu tamamen çöpe atmaz
    - Sadece domain içi daha mantıklı sıralama yapar
    """
    tokens = tokenize_query(query)

    # Token genişletme artık domain rule engine üzerinden yapılır.
    expanded_tokens = expand_tokens(tokens)

    reranked = []

    for item in results:
        # FAISS skoru temel skor olarak korunuyor.
        base_score = float(item.get("score") or 0.0)
        rerank_score = base_score

        title = str(item.get("title") or "").lower()
        content = str(item.get("content") or "").lower()
        category = str(item.get("category") or "").lower()
        product_code = str(item.get("product_code") or "").lower()
        source = str(item.get("source") or "").lower()
        brand = str(item.get("brand") or "").lower()
        part_group = str(item.get("part_group") or "").lower()
        metadata = str(item.get("metadata") or "").lower()
        item_type = str(item.get("item_type") or "").lower()

        blob = f"{title} {content} {category} {product_code} {source} {brand} {part_group} {metadata}"

        matched_tokens = set()

        for token in expanded_tokens:
            token = token.lower()

            # Başlık eşleşmesi en güçlü sinyal.
            if token in title:
                rerank_score += 0.35
                matched_tokens.add(token)

            # Ürün kodu eşleşmesi güçlü sinyal.
            if token in product_code:
                rerank_score += 0.30
                matched_tokens.add(token)

            # Kategori eşleşmesi orta güçlü sinyal.
            if token in category:
                rerank_score += 0.18
                matched_tokens.add(token)

            # İçerik eşleşmesi destekleyici sinyal.
            if token in content:
                rerank_score += 0.12
                matched_tokens.add(token)

            # Metadata / part_group destekleyici sinyal.
            if token in metadata or token in part_group:
                rerank_score += 0.10
                matched_tokens.add(token)

        # Genel bilgi sorularında text kayıtlarını öne al.
        if item_type == "text":
            rerank_score += 0.15

        # Genel semantic QA'da görseller biraz geriye düşsün.
        if item_type == "image":
            rerank_score -= 0.10

        # Otomotiv domain'ine özel semantic boost/penalty kuralları.
        rerank_score = apply_automotive_semantic_rules(
            item=item,
            expanded_tokens=expanded_tokens,
            current_score=rerank_score
        )

        item["semantic_rerank_score"] = round(rerank_score, 4)
        item["semantic_matched_keywords"] = sorted(list(matched_tokens))
        item["match_type"] = "semantic_search_tool"

        reranked.append(item)

    reranked = sorted(
        reranked,
        key=lambda x: x.get("semantic_rerank_score", x.get("score", 0)),
        reverse=True
    )

    return reranked

def semantic_search_tool(query, top_k=5):
    """
    Genel semantic search tool.

    Akış:
    1. FAISS ile semantic sonuçları getirir.
    2. Sonuçları keyword + metadata sinyalleriyle yeniden sıralar.
    3. Duplicate item_id kayıtlarını temizler.
    """
    # FAISS'ten biraz fazla sonuç çekiyoruz.
    # Çünkü doğru kayıt bazen ilk 5 dışında olabilir.
    results = search_by_text(query, top_k=top_k * 4)

    for item in results:
        item["match_type"] = "semantic_search_tool"

    # FAISS sonuçlarını domain-aware keyword sinyalleriyle yeniden sırala.
    results = apply_semantic_rerank(results, query)

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