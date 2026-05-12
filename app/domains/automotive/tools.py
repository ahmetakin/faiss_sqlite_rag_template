"""
Automotive retrieval tools.

Bu dosya otomotiv domain'ine özel retrieval tool implementasyonlarını tutar.

Tool listesi:
- product_code_tool
- image_search_tool
- recommendation_tool
- semantic_search_tool
- technical_qa_tool

Bu tool'lar SQLite metadata search, FAISS semantic search ve domain rerank
kurallarını birlikte kullanır.
"""

from app.core.db import (
    search_items_by_product_code,
    search_items_by_filters,
)

from app.core.hybrid_search_engine import hybrid_text_search

from app.domains.automotive.search_rules import search_technical_by_keywords

from app.core.search import search_by_text
from app.core.tools import deduplicate_results

from app.domains.automotive.rules import (
    expand_tokens,
    apply_automotive_semantic_rules,
)


def get_product_family(code: str):
    """
    Ürün kodundan aile prefix'i çıkarır.

    Örnek:
    ENGINE-OIL-AKN -> ENGINE-OIL
    BAT-12V-BOSCH -> BAT-12V

    Exact ürün kodu bulunamazsa aynı ailedeki ürünleri getirmek için kullanılır.
    """
    parts = code.split("-")

    if len(parts) >= 2:
        return "-".join(parts[:2])

    return code


def product_code_tool(route, top_k=5):
    """
    Ürün kodu arama tool'u.

    Akış:
    1. Önce product_code exact search yapılır.
    2. Exact sonuç yoksa ürün ailesi fallback yapılır.

    Örnek:
    ENGINE-OIL-CASTROL -> exact bulunur.
    ENGINE-OIL-AKN -> exact yoksa ENGINE-OIL ailesinden benzer ürünler gelir.
    """
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
    """
    Görsel arama tool'u.

    Akış:
    1. SQLite metadata filter ile aday görseller alınır.
    2. Eğer strict_family varsa daha fazla aday çekilir.
    3. retrieval_service strict_family_filter ile yanlış aileleri eler.

    Örnek:
    "araba aküsü görselini getir"
    -> strict_family=battery
    -> sadece BAT-12V prefix'li aküler kalır.
    """
    limit = top_k * 5

    if route.get("strict_family"):
        limit = top_k * 10

    results = search_items_by_filters(
        query_terms=route.get("query_terms") or [],
        only_images=True,
        brand=route.get("brand"),
        part_keywords=route.get("part_keywords"),
        limit=limit,
    )

    for item in results:
        item["match_type"] = "image_metadata_tool"
        item["score"] = item.get("score") or 0.95

    return deduplicate_results(results)[:limit]


def recommendation_tool(route, top_k=5):
    """
    Öneri / karşılaştırma tool'u.

    Bu tool aday ürünleri getirir.
    Asıl recommendation_score hesabı retrieval_rules.py içinde yapılır.
    """
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
    Kullanıcı sorgusunu anlamlı token'lara böler.

    Amaç:
    - Zayıf kelimeleri atmak
    - Semantic sonuçlarda keyword sinyali üretmek
    """
    stopwords = {
        "ne", "nedir", "nasıl", "neden", "kaç", "mi", "mı", "mu", "mü",
        "ve", "veya", "bir", "bu", "şu", "için", "ile", "gibi",
        "var", "kapsamında", "kapsamı", "şartları", "nelerdir",
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
    FAISS'ten gelen semantic sonuçları domain kurallarına göre yeniden sıralar.

    Neden?
    FAISS skoru tek başına bazen yeterli değildir.
    Örneğin "araç aküsü garanti" sorusunda EV batarya garanti dokümanı da yakın gelebilir.
    Burada title/content/product_code/metadata + automotive rules ile yeniden skorlanır.
    """
    tokens = tokenize_query(query)

    # Synonym expansion domain tarafındaki rules.py üzerinden yapılır.
    expanded_tokens = expand_tokens(tokens)

    reranked = []

    for item in results:
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

        matched_tokens = set()

        for token in expanded_tokens:
            token = token.lower()

            if token in title:
                rerank_score += 0.35
                matched_tokens.add(token)

            if token in product_code:
                rerank_score += 0.30
                matched_tokens.add(token)

            if token in category:
                rerank_score += 0.18
                matched_tokens.add(token)

            if token in content:
                rerank_score += 0.12
                matched_tokens.add(token)

            if token in metadata or token in part_group:
                rerank_score += 0.10
                matched_tokens.add(token)

        # Genel bilgi sorularında text kayıtları daha değerlidir.
        if item_type == "text":
            rerank_score += 0.15

        # Genel semantic QA'da görseller biraz geriye düşsün.
        if item_type == "image":
            rerank_score -= 0.10

        # Otomotiv domain'e özel rule engine.
        rerank_score = apply_automotive_semantic_rules(
            item=item,
            expanded_tokens=expanded_tokens,
            current_score=rerank_score,
        )

        item["semantic_rerank_score"] = round(rerank_score, 4)
        item["semantic_matched_keywords"] = sorted(list(matched_tokens))
        item["match_type"] = item.get("match_type") or "semantic_search_tool"

        reranked.append(item)

    return sorted(
        reranked,
        key=lambda x: x.get("semantic_rerank_score", x.get("score", 0)),
        reverse=True,
    )


def semantic_search_tool(query, top_k=5):
    """
    Genel semantic search tool.

    Yeni akış:
    1. FAISS + BM25 hybrid search ile adayları getirir.
    2. Automotive semantic rerank kurallarını uygular.
    3. Duplicate item_id kayıtlarını temizler.
    4. top_k sonucu döndürür.

    Neden hybrid?
    - FAISS anlam benzerliği yakalar.
    - BM25 birebir keyword eşleşmesini yakalar.
    - İkisi birleşince garanti, ürün kodu, teknik terim gibi sorgular daha sağlam çalışır.
    """

    # Hybrid search biraz fazla aday getirir.
    # Çünkü domain rerank doğru kaydı üst sıraya taşıyabilir.
    results = hybrid_text_search(
        query=query,
        top_k=top_k * 4,
        candidate_k=30,
        faiss_weight=0.65,
        bm25_weight=0.35,
    )

    for item in results:
        item["match_type"] = "semantic_hybrid_search_tool"

    # Hybrid sonuçları tekrar domain-aware semantic rerank'ten geçiriyoruz.
    results = apply_semantic_rerank(results, query)

    return deduplicate_results(results)[:top_k]


def technical_qa_tool(query, top_k=5, route=None):
    """
    Teknik soru-cevap tool'u.

    Akış:
    1. Önce SQLite keyword search yapılır.
       Bu teknik dokümanlarda daha deterministik sonuç verir.
    2. Sonuç yoksa FAISS semantic fallback çalışır.
    3. Fallback sonuçları teknik skor ile yeniden sıralanır.
    """

    # 1) Önce SQLite keyword search
    keyword_results = search_technical_by_keywords(query, limit=top_k)

    if keyword_results:
        for item in keyword_results:
            item["match_type"] = "technical_keyword_db"

        return deduplicate_results(keyword_results)[:top_k]

    # 2) Fallback: FAISS semantic search
    results = search_by_text(query, top_k=top_k * 5)

    q = query.lower()
    strict_family = route.get("strict_family") if route else None
    part_keywords = route.get("part_keywords") if route else []

    def technical_score(item):
        """
        FAISS fallback sonuçlarını teknik QA için yeniden skorlar.
        """
        score = float(item.get("score") or 0.0)

        title = str(item.get("title") or "").lower()
        content = str(item.get("content") or "").lower()
        category = str(item.get("category") or "").lower()
        product_code = str(item.get("product_code") or "").upper()
        part_group = str(item.get("part_group") or "").lower()
        item_type = str(item.get("item_type") or "").lower()

        blob = f"{title} {content} {category} {product_code.lower()} {part_group}"

        # Teknik cevaplarda text dokümanı genelde görselden daha değerlidir.
        if item_type == "text":
            score += 0.30

        # Teknik/servis/bakım kategorilerini öne al.
        if category in ["teknik_bilgi", "servis", "bakim", "garanti", "bilgi"]:
            score += 0.20

        # Görseller teknik QA'da geriye düşsün.
        if item_type == "image":
            score -= 0.20

        # Query tokenları içerikte geçiyorsa küçük boost ver.
        for token in q.split():
            if len(token) >= 4 and token in blob:
                score += 0.05

        # Router'dan gelen parça keywordleri varsa boost ver.
        for kw in part_keywords or []:
            if kw.lower() in blob:
                score += 0.12

        # Strict family özel boost/penalty.
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
        reverse=True,
    )

    return deduplicate_results(scored)[:top_k]