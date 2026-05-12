"""
Automotive search rules.

Bu dosya otomotiv domain'ine özel keyword tabanlı arama kurallarını tutar.

Core/db.py sadece veritabanı erişimi yapmalı.
Teknik soru-cevap için keyword scoring gibi domain mantıkları burada durmalı.
"""

from app.core.db import get_connection, row_to_item


TECHNICAL_STOPWORDS = {
    "ne", "nedir", "nasıl", "neden", "olur", "olursa",
    "kaç", "mi", "mı", "mu", "mü", "ve", "veya",
    "bir", "bu", "şu", "için", "ile", "gibi",
    "yapılır", "yapılmalı", "edilir", "etkilenir",
    "sistemi", "arızalanırsa", "yanarsa", "koparsa",
}


STRONG_SINGLE_TERMS = {
    "dpf", "abs", "esp", "egr", "maf", "tpms", "vin", "hud",
}


def tokenize_technical_query(query: str):
    """
    Teknik soruyu anlamlı keyword listesine çevirir.

    Amaç:
    - Zayıf soru kelimelerini atmak
    - Teknik kavramları korumak
    """
    raw_tokens = (
        query.lower()
        .replace("?", " ")
        .replace(",", " ")
        .replace(".", " ")
        .replace(":", " ")
        .split()
    )

    return [
        token.strip()
        for token in raw_tokens
        if len(token.strip()) >= 3 and token.strip() not in TECHNICAL_STOPWORDS
    ]


def score_technical_item(item: dict, keywords: list[str]):
    """
    Bir text dokümanının teknik sorguya ne kadar uyduğunu skorlar.

    Skor mantığı:
    - Başlık eşleşmesi çok güçlü
    - Product code / part_group güçlü
    - Category orta
    - Content destekleyici
    - Metadata zayıf destekleyici
    """
    title = str(item.get("title") or "").lower()
    content = str(item.get("content") or "").lower()
    category = str(item.get("category") or "").lower()
    product_code = str(item.get("product_code") or "").lower()
    part_group = str(item.get("part_group") or "").lower()
    metadata = str(item.get("metadata") or "").lower()

    score = 0.0
    matched_tokens = set()

    for kw in keywords:
        if kw in title:
            score += 5.0
            matched_tokens.add(kw)

        if kw in product_code:
            score += 4.0
            matched_tokens.add(kw)

        if kw in part_group:
            score += 4.0
            matched_tokens.add(kw)

        if kw in category:
            score += 2.0
            matched_tokens.add(kw)

        if kw in content:
            score += 1.5
            matched_tokens.add(kw)

        if kw in metadata:
            score += 1.0
            matched_tokens.add(kw)

    return score, matched_tokens


def search_technical_by_keywords(query: str, limit: int = 10):
    """
    Teknik QA için SQLite text kayıtları üzerinde keyword scoring yapar.

    Bu FAISS yerine geçmez.
    Ama teknik bilgi kayıtlarında deterministik ilk adayları bulmak için kullanılır.
    """
    keywords = tokenize_technical_query(query)

    if not keywords:
        return []

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM items
    WHERE item_type = 'text'
    """)

    rows = cur.fetchall()
    conn.close()

    scored_results = []

    for row in rows:
        item = row_to_item(row)

        score, matched_tokens = score_technical_item(
            item=item,
            keywords=keywords,
        )

        # En az 2 anlamlı token eşleşsin.
        # Ancak DPF, ABS gibi kısa güçlü teknik terimler tek başına yeterlidir.
        if len(matched_tokens) < 2:
            if not any(term in matched_tokens for term in STRONG_SINGLE_TERMS):
                continue

        item["score"] = round(score, 4)
        item["keyword_score"] = round(score, 4)
        item["matched_keywords"] = list(matched_tokens)
        item["match_type"] = "technical_keyword_db"

        scored_results.append(item)

    scored_results = sorted(
        scored_results,
        key=lambda x: x.get("keyword_score", 0),
        reverse=True,
    )

    return scored_results[:limit]